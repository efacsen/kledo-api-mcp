# Requirements — Milestone v1.1: MCP SDK Modernization

## Active Requirements

### SDK Layer

- [ ] **SDK-01**: Developer can install the server with `mcp>=1.0.0` — `pyproject.toml` bumped, old `mcp>=0.9.0` removed
- [ ] **SDK-02**: Server initializes via `FastMCP` with a `lifespan` hook that builds and tears down the `KledoAPIClient` — replaces the `initialize_client()` singleton pattern in `server.py`
- [ ] **SDK-03**: Server exposes an `instructions` field injected into Claude's system prompt on every session (domain facts: invoice status codes 1/2/3, commission uses pre-tax subtotal from paid invoices only, always call list before detail because IDs are not guessable, amounts in IDR)
- [ ] **SDK-04**: All tool errors return `{"isError": True, "content": [...]}` with a recovery hint — Claude can distinguish errors from valid results and act on them

### Tool Interface

- [x] **IFACE-01**: All tool modules migrated to `@mcp.tool()` decorator pattern — `get_tools()` and `handle_tool()` deleted from every module (affects: analytics, commission, contacts, deliveries, financial, invoices, orders, products, revenue, sales_analytics, utilities)
- [x] **IFACE-02**: All tools carry `annotations={"readOnlyHint": True, "openWorldHint": True}` — eliminates confirmation dialogs in Claude Desktop and Claude Code
- [x] **IFACE-03**: `commission_report`, `analytics_compare`, and `revenue_summary` emit `ctx.report_progress()` at meaningful checkpoints during multi-page API fetches

### Tool Quality

- [ ] **QUAL-01**: All tool descriptions rewritten to the pattern: what it does → what it returns → what it does NOT do → when to use a sibling tool instead
- [ ] **QUAL-02**: All input parameter fields carry `.describe()` strings with type, format constraints, and default value notes
- [ ] **QUAL-03**: Tool return format changed from raw markdown tables to structured text with IDs Claude can use in follow-up calls (truncate large results and say so)

### Tool Consolidation

- [ ] **CONS-01**: Near-duplicate tool pairs merged via mode/action parameter — target 14-16 dedicated tools (audit of 24 current tools determines exact merges; list+get pairs and sub-mode tools are candidates)
- [ ] **CONS-02**: `src/routing/` deleted except `date_parser.py` which moves to `src/utils/date_parser.py` and is wired into tool handlers that accept date phrases
- [ ] **CONS-03**: `rapidfuzz` evaluated post-routing deletion — removed from `pyproject.toml` if no longer needed at top level (retained only if still directly used in tool handler logic)

### Compatibility

- [x] **COMPAT-01**: Existing HTTP transport (bearer token auth, CORS, `/health` endpoint from Phases 1-2) continues to work unchanged after `server.py` rewrite
- [x] **COMPAT-02**: stdio transport continues to work for Claude Desktop users — no regression on existing configuration

## Future Requirements

- Remote HTTP transport via jlowin's `fastmcp` 3.x (one-line transport swap when needed) — deferred to Phase 4+
- Docker single-command deployment — deferred, pending v1.1 stabilization
- Per-user API key isolation for multi-user deployment — deferred
- `structuredContent` + `outputSchema` typed outputs — deferred until client support is widespread (spec-stable but patchy client coverage as of 2026-04)
- MCP elicitation for interactive parameter input — deferred until Claude Desktop support confirmed

## Out of Scope

- `search_tools` / `run_tool` catalog architecture — tool count (24→14-16) stays in the dedicated-tool sweet spot; catalog pattern adds round-trip overhead without benefit at this scale
- jlowin's `fastmcp` 3.x as the migration target — using official `mcp.server.fastmcp.FastMCP` for Anthropic SDK compatibility; 3.x migration path preserved for future HTTP phase
- Write operations — all tools remain read-only per existing design
- OAuth flow — API key auth is sufficient for self-hosted model
- Multi-tenant hosted service — each user self-hosts their own instance

## Traceability

| REQ-ID | Phase | Notes |
|--------|-------|-------|
| SDK-01 | Phase 3 | SDK Foundation |
| SDK-02 | Phase 3 | SDK Foundation |
| SDK-03 | Phase 3 | SDK Foundation |
| SDK-04 | Phase 3 | SDK Foundation |
| IFACE-01 | Phase 4 | Tool Interface Migration |
| IFACE-02 | Phase 4 | Tool Interface Migration |
| IFACE-03 | Phase 4 | Tool Interface Migration |
| COMPAT-01 | Phase 4 | Tool Interface Migration |
| COMPAT-02 | Phase 4 | Tool Interface Migration |
| QUAL-01 | Phase 5 | Tool Quality |
| QUAL-02 | Phase 5 | Tool Quality |
| QUAL-03 | Phase 5 | Tool Quality |
| CONS-01 | Phase 6 | Tool Consolidation |
| CONS-02 | Phase 6 | Tool Consolidation |
| CONS-03 | Phase 6 | Tool Consolidation |
