# MCP Server Modernization Plan

Audit and upgrade roadmap for migrating `kledo-api-mcp` from the pre-1.0 MCP SDK pattern to
current best practices. Written against the state of the codebase on 2026-04-09.

---

## Overall Grade: B− (76/100)

| Category | Grade | Score | Summary |
|---|---|---|---|
| Tool Design | C+ | 65 | 24 tools is too many; descriptions are too vague |
| Routing Architecture | D | 45 | `src/routing/` is sophisticated but never called |
| Return Format | C | 60 | Markdown strings hurt Claude's follow-up reasoning |
| Protocol Compliance | A− | 88 | Correct pattern, but on an outdated SDK version |
| Code Quality | A− | 87 | mypy strict, async, type hints — genuinely good |
| Security | A | 92 | API key auth, no hardcoded secrets, read-only |
| Testing | C+ | 62 | 45% coverage floor is low for financial data |
| Distribution Model | C | 58 | Local stdio only — every user must install locally |
| Documentation | A | 94 | README, ARCHITECTURE, CLAUDE.md all excellent |

---

## Critical Issues

### 1. SDK Version — `mcp>=0.9.0` is Pre-1.0

The server uses the raw low-level pattern from before MCP reached 1.0:

```python
# Current (src/server.py)
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("kledo-crm")

@server.list_tools()
async def list_tools() -> list[Tool]: ...

@server.call_tool()
async def call_tool(name, arguments): ...

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())
```

MCP 1.x ships `FastMCP` inside the official `mcp` package (`mcp.server.fastmcp`). It removes all
of this boilerplate and unlocks features that don't exist in 0.9: tool annotations, server
`instructions`, progress notifications, structured outputs, and protocol-level logging.

**Fix:** Bump to `mcp>=1.0.0` in `pyproject.toml`.

---

### 2. Dead Code — `src/routing/` Is Never Called

`src/routing/` contains ~1,500 lines of sophisticated natural language routing:

- `router.py` — orchestrator, returns top-5 tool suggestions
- `patterns.py` — ~50 idiomatic EN/ID phrase patterns
- `synonyms.py` — ~80 business term mappings (piutang → receivable, omzet → sales)
- `fuzzy.py` — RapidFuzz at 80% threshold for typo tolerance
- `scorer.py` — keyword extraction and relevance scoring
- `date_parser.py` — "bulan ini", "Q1 2025", "last 30 days" → ISO date tuples

None of this is imported or called by `server.py`. It was built to replicate Claude's natural
language understanding inside the server — but that's backwards. Claude already does NL routing.

**Options (pick one):**

| Option | Effort | Recommendation |
|---|---|---|
| Delete the entire `src/routing/` directory | 10 min | If you want a clean slate |
| Extract only `date_parser.py` → `src/utils/` | 30 min | Best: date normalization is genuinely useful inside tool handlers |
| Wire router into a `search_tools` catalog tool | 2–4 hrs | Best if reducing tool count (see §4) — the routing logic finally earns its keep |

---

### 3. Error Returns — Semantically Wrong

All tool errors are returned as plain `TextContent`. Claude cannot distinguish an error from a
valid result and will treat the error message as data.

```python
# Current (src/server.py:234-237) — WRONG
except Exception as e:
    error_msg = f"Error executing tool {name}: {str(e)}"
    return [TextContent(type="text", text=error_msg)]
```

```python
# Correct — MCP isError pattern
except Exception as e:
    return {
        "isError": True,
        "content": [{"type": "text", "text": f"Error: {e}. Try invoice_list to find valid IDs."}]
    }
```

The `isError: true` flag lets Claude decide to retry, ask for clarification, or surface the
error to the user — instead of reasoning over a string that says "Error executing tool".

---

### 4. Tool Count — 24 Is Too Many

Every tool's name + description + full JSON schema is injected into Claude's context window on
every request. At 24 tools with non-trivial schemas, that's ~3,000–5,000 tokens burned before
any reasoning starts. This degrades response quality and increases cost.

MCP tool count guidance:
- **1–15 tools** → one tool per action (sweet spot)
- **15–30 tools** → audit for merges
- **30+ tools** → search + execute pattern

You previously had 41 tools and consolidated to 24. The right end state is **8–10 promoted
tools** for the highest-frequency operations, and the remaining 14–16 accessible via a
`search_tools` / `run_tool` catalog pair.

**Proposed split:**

| Keep as dedicated tool | Reason |
|---|---|
| `invoice_list` | Most-used entry point |
| `invoice_detail` | Always follows `invoice_list` |
| `contact_detail` | Core CRM lookup |
| `revenue_summary` | Primary KPI for the business |
| `outstanding_receivables` | High business value, frequently queried |
| `commission_calculate` | Specific, named use case |
| `product_list` | Inventory lookups |
| `utility_cache` | Maintenance / diagnostics |

**Move to catalog behind `search_tools` + `run_tool`:**
All analytics, comparison, delivery, order, financial report, and secondary tools.

The `src/routing/` fuzzy matcher + synonym map is the correct backend for `search_tools`.
This is the one scenario where that code should be resurrected.

---

### 5. Tool Descriptions — Too Vague for Claude

Tool descriptions are the only thing Claude reads before deciding which tool to call. Vague
descriptions cause wrong tool selection.

**Current (too vague):**
```python
Tool(name="invoice_list", description="List sales or purchase invoices", ...)
```

**Better (tells Claude when, what it returns, and what it does NOT do):**
```
List Kledo invoices filtered by type (sales/purchase), date range, status, or customer name.
Returns paginated results with status code, total amount, and contact name.
For line-item detail, use invoice_detail after getting an ID from here.
Does NOT filter by sales rep — use financial_sales_summary for that.
```

This pattern — what it does, what it returns, what it does NOT do, when to use a sibling — is
the difference between Claude picking the right tool vs. hallucinating parameters.

---

### 6. Return Format — Markdown Strings Hurt Downstream Reasoning

All tools return formatted markdown tables:

```python
return f"## Invoice List\n\n| # | Customer | Amount |\n|---|---|---|\n..."
```

If Claude needs to do follow-up reasoning (e.g., "which of these has the highest balance?"), it
has to re-parse your markdown table back into data. This is fragile and wastes context.

**Better:** Return compact, structured prose or JSON with key values clearly labeled. Include IDs
Claude will need for follow-up calls. Truncate large results and say so.

```python
# Example: structured text Claude can reason over
return (
    f"Found {total} invoices. Showing {len(items)} of {total}.\n\n"
    + "\n".join(
        f"- ID:{inv['id']} | {inv['contact_name']} | Rp{inv['amount']:,.0f} | {inv['status']}"
        for inv in items
    )
    + ("\n\n(More results available — narrow date range or add search term)" if has_more else "")
)
```

---

## Modernization Roadmap

### Phase 1 — Quick wins (1–2 hours, zero risk)

**1a. Bump SDK version**
```toml
# pyproject.toml
"mcp>=1.0.0",   # was mcp>=0.9.0
```

**1b. Migrate server.py to FastMCP**

```python
# src/server.py — replaces ~253 lines with ~80
from mcp.server.fastmcp import FastMCP
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(server: FastMCP):
    """Initialize and tear down the API client."""
    global _client
    _client = await _build_client()
    yield
    # cleanup if needed

mcp = FastMCP(
    "kledo-crm",
    lifespan=lifespan,
    instructions=(
        "Read-only Kledo accounting server for a paint distribution company. "
        "Invoice statuses: 1=Unpaid, 2=Partial, 3=Paid. "
        "Commission is calculated from pre-tax subtotal (paid invoices only). "
        "Always use invoice_list or contact_detail before invoice_detail — IDs are not guessable. "
        "Amounts are in Indonesian Rupiah (IDR)."
    ),
)
```

The `instructions` string is injected into Claude's system prompt verbatim. This is the
single highest-leverage change — it corrects tool-choice behavior without touching tool code.

**1c. Add `readOnlyHint: True` to all tools**

Since every tool in this server is read-only, all of them qualify. This lets Claude Desktop
auto-approve tool calls without asking the user each time.

```python
# In get_tools() for each module, add annotations to every Tool:
Tool(
    name="invoice_list",
    description="...",
    inputSchema={...},
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
```

**1d. Fix isError returns in server.py**

```python
# src/server.py call_tool handler
except Exception as e:
    return {
        "isError": True,
        "content": [{"type": "text", "text": f"Tool '{name}' failed: {e}"}],
    }
```

---

### Phase 2 — Tool quality (2–4 hours)

**2a. Rewrite tool descriptions** using the pattern: what it does → what it returns → what it
does NOT do → when to use a sibling tool instead.

**2b. Add parameter `.describe()` strings** to every field in every inputSchema. These show up
in the schema Claude sees. Example:

```python
"date_from": {
    "type": "string",
    "description": "Start date in YYYY-MM-DD format. Defaults to 30 days ago if omitted."
},
```

**2c. Add progress reporting** to the three slow tools using FastMCP's `Context`:

```python
# src/tools/commission.py
from mcp.server.fastmcp import Context

async def _commission_report(arguments: dict, client: KledoAPIClient, ctx: Context) -> str:
    await ctx.report_progress(0, 100, "Fetching paid invoices...")
    invoices = await fetch_all_pages(client, arguments)
    await ctx.report_progress(50, 100, "Calculating commission tiers...")
    result = calculate_tiers(invoices)
    await ctx.report_progress(100, 100, "Complete")
    return format_report(result)
```

Tools that benefit from progress: `commission_report`, `analytics_compare`, `revenue_summary`
(when paginating many months).

---

### Phase 3 — Architecture (4–8 hours)

**3a. Reduce promoted tools to 8–10**

Merge the 14–16 lower-frequency tools into a catalog. The catalog lives server-side as a dict
of `{tool_id: {description, param_schema, handler}}`. Two new tools replace them:

```python
@mcp.tool(annotations={"readOnlyHint": True})
async def search_tools(intent: str) -> str:
    """
    Find available tools matching your intent. Returns tool IDs, descriptions, and
    parameter schemas. Call this when you're unsure which tool to use, or when the
    dedicated tools don't cover what you need.
    """
    # Use src/routing/scorer.py + fuzzy.py here
    matches = route_query(intent)
    return format_catalog_matches(matches)

@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
async def run_tool(tool_id: str, params: dict) -> str:
    """
    Execute a catalog tool by ID. Get the ID and params schema from search_tools first.
    """
    return await dispatch_catalog_tool(tool_id, params, client)
```

**3b. Resurrect `src/routing/` for `search_tools`**

The fuzzy matcher, synonym map, and scorer are the right backend for ranking catalog results.
Move `date_parser.py` to `src/utils/date_parser.py` for use in tool handlers regardless.
Delete `src/routing/patterns.py` — the idiomatic patterns belong in tool descriptions, not
server-side code.

**3c. Migrate to FastMCP decorator-based tools** (optional, but reduces boilerplate)

Each `get_tools()` / `handle_tool()` module pair can be replaced with decorated functions
registered on the `mcp` instance. This eliminates the dispatch routing in `server.py` entirely.

```python
# Before: 11 modules × get_tools() + handle_tool() + prefix routing in server.py
# After: decorated functions, FastMCP handles dispatch automatically

@mcp.tool(annotations={"readOnlyHint": True})
async def invoice_list(type: Literal["sales", "purchase"], ...) -> str:
    """..."""
    client = get_client()
    return await invoices._list_invoices({"type": type, ...}, client)
```

---

### Phase 4 — Distribution (optional, significant effort)

The current model requires every user to clone the repo, install Python 3.11+, and configure
Claude Desktop manually. For a business tool, consider a remote HTTP server:

```python
# Run as HTTP instead of stdio — single line change with FastMCP
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
    # Users add: claude mcp add --transport http kledo https://your-server/mcp
```

Benefits: one deployment, zero per-user install, centralized config, push updates without
user action. The existing Docker setup in the README makes this straightforward.

---

## File-Level Change Summary

| File | Change | Priority |
|---|---|---|
| `pyproject.toml` | Bump `mcp>=1.0.0`, remove `rapidfuzz` if routing deleted | Phase 1 |
| `src/server.py` | Rewrite with FastMCP + lifespan + instructions + isError | Phase 1 |
| `src/tools/*.py` | Add `annotations` to all Tool objects | Phase 1 |
| `src/tools/*.py` | Rewrite all tool descriptions | Phase 2 |
| `src/tools/*.py` | Add `.description` to all inputSchema fields | Phase 2 |
| `src/tools/commission.py` | Add `ctx.report_progress` calls | Phase 2 |
| `src/tools/analytics.py` | Add `ctx.report_progress` calls | Phase 2 |
| `src/tools/revenue.py` | Add `ctx.report_progress` calls | Phase 2 |
| `src/routing/` | Delete OR wire into `search_tools` catalog tool | Phase 3 |
| `src/utils/date_parser.py` | Extract from routing, use in tool handlers | Phase 3 |

---

## What to Keep As-Is

These are already well-built and don't need changes:

- `src/kledo_client.py` — async HTTP client with caching is solid
- `src/auth.py` — dual-method auth with auto-refresh is correct
- `src/cache.py` — multi-tier TTL cache is well-designed
- `src/entities/` — Pydantic models are correct
- `config/endpoints.yaml` — configuration-driven endpoints is the right approach
- `config/cache_config.yaml` — TTL tiers are sensible
- `tests/` — structure is good, raise the coverage floor to 70% over time
- `ARCHITECTURE.md`, `README.md`, `CLAUDE.md` — documentation is excellent

---

## Quick Reference: FastMCP 1.x vs Old Pattern

| Old pattern (0.9) | FastMCP 1.x |
|---|---|
| `from mcp.server import Server` | `from mcp.server.fastmcp import FastMCP` |
| `@server.list_tools()` + `@server.call_tool()` | `@mcp.tool()` decorator |
| Manual `if name.startswith("invoice_"):` routing | Automatic dispatch by function name |
| No `instructions` support | `FastMCP("name", instructions="...")` |
| No tool annotations | `@mcp.tool(annotations={"readOnlyHint": True})` |
| No progress API | `ctx.report_progress(current, total, message)` |
| `stdio_server()` context manager | `mcp.run()` handles transport |
| Error as plain TextContent | `{"isError": True, "content": [...]}` |
| No lifespan hooks | `@asynccontextmanager async def lifespan(server)` |

---

*Audit performed: 2026-04-09. SDK reference: `mcp>=1.0.0` (FastMCP included in official package).*
