# Roadmap: Kledo MCP Server

## Milestones

- ✅ **v1.0 Public Release Foundation** - Phases 1-2 (shipped 2026-04-02)
- 🚧 **v1.1 MCP SDK Modernization** - Phases 3-6 (in progress)

## Phases

<details>
<summary>✅ v1.0 Public Release Foundation (Phases 1-2) - SHIPPED 2026-04-02</summary>

### Phase 1: HTTP Transport
**Goal**: Server is reachable over HTTP for remote MCP clients alongside existing stdio
**Plans**: Complete

### Phase 2: Security Hardening
**Goal**: HTTP endpoint is safe for public exposure with bearer token auth and secret redaction
**Plans**: Complete

</details>

### 🚧 v1.1 MCP SDK Modernization (In Progress)

**Milestone Goal:** Migrate from pre-1.0 raw `Server` pattern to native `FastMCP` (`mcp>=1.0.0`) with full `@mcp.tool()` decorator adoption, eliminating the `get_tools()`/`handle_tool()` dispatch layer, and reducing the tool surface to 14-16 precisely-described dedicated tools.

- [ ] **Phase 3: SDK Foundation** - Rewrite `server.py` to `FastMCP` with lifespan hook, `instructions` field, and correct error returns
- [x] **Phase 4: Tool Interface Migration** - Migrate all 11 tool modules to `@mcp.tool()` decorator pattern with `readOnlyHint`, progress reporting, and transport compatibility preserved (completed 2026-04-10)
- [ ] **Phase 5: Tool Quality** - Rewrite all tool descriptions, add parameter `.describe()` strings, and improve return format for AI consumption
- [ ] **Phase 6: Tool Consolidation** - Merge 24 tools down to 14-16, delete dead routing code, clean up dependencies

## Phase Details

### Phase 3: SDK Foundation
**Goal**: The server boots via `FastMCP`, injects domain context into every Claude session, and returns machine-readable errors that Claude can act on
**Depends on**: Phase 2
**Requirements**: SDK-01, SDK-02, SDK-03, SDK-04
**Success Criteria** (what must be TRUE):
  1. `pyproject.toml` declares `mcp>=1.0.0` and the server starts without import errors from the old SDK
  2. `KledoAPIClient` is created inside a `lifespan` hook and torn down cleanly on server shutdown — no singleton pattern remains in `server.py`
  3. Any new Claude session receives injected instructions covering invoice status codes, commission formula, and ID-lookup guidance without the developer prompting for it
  4. When a Kledo API call fails, Claude receives a response with `isError: true` and a recovery hint (e.g. "check KLEDO_API_KEY") rather than a raw exception traceback
**Plans**: 2 plans
  - [ ] 03-01-PLAN.md — Wave 0: rewrite tests/test_server.py to lock the FastMCP contract (SDK-01..04 test scaffold)
  - [ ] 03-02-PLAN.md — Wave 1: bump mcp>=1.0.0 + rewrite src/server.py to FastMCP with lifespan, instructions, and ToolError dispatch bridge

### Phase 4: Tool Interface Migration
**Goal**: Every tool is registered via `@mcp.tool()` decorator — the `get_tools()` and `handle_tool()` dispatch pattern is gone from all 11 modules, compatibility transports are unbroken
**Depends on**: Phase 3
**Requirements**: IFACE-01, IFACE-02, IFACE-03, COMPAT-01, COMPAT-02
**Success Criteria** (what must be TRUE):
  1. All 11 tool modules (`analytics`, `commission`, `contacts`, `deliveries`, `financial`, `invoices`, `orders`, `products`, `revenue`, `sales_analytics`, `utilities`) have `@mcp.tool()` decorated functions and no `get_tools()` or `handle_tool()` exports
  2. Claude Desktop connected via stdio can call any tool and receive a response — no regression from the migration
  3. Existing HTTP bearer-token endpoint (`/mcp`) and `/health` continue to respond correctly after the `server.py` rewrite
  4. All tools report `readOnlyHint: True` and `openWorldHint: True` — Claude Desktop no longer shows confirmation dialogs for any tool call
  5. `commission_report`, `analytics_compare`, and `revenue_summary` emit progress updates during multi-page API fetches so the client shows a live indicator
**Plans**: 3 plans
  - [x] 04-01-PLAN.md — Wave 0: write contract tests for the new @mcp.tool() interface (RED until migration complete)
  - [x] 04-02-PLAN.md — Wave 1: strip get_tools/handle_tool from all 11 modules + rewrite server.py @mcp.tool() registrations
  - [x] 04-03-PLAN.md — Wave 2: add readOnlyHint/openWorldHint annotations + ctx.report_progress() to 3 tools + transport regression checks

### Phase 5: Tool Quality
**Goal**: Every tool description tells Claude exactly what the tool does, what it returns, and when to pick a sibling tool instead — parameter types and defaults are explicit
**Depends on**: Phase 4
**Requirements**: QUAL-01, QUAL-02, QUAL-03
**Success Criteria** (what must be TRUE):
  1. Every tool description follows the four-part pattern: what it does, what it returns, what it does NOT do, when to use a sibling tool instead
  2. Every input parameter has a `.describe()` string stating its type, format constraints, and default value
  3. Tool responses present IDs Claude can use in follow-up calls (e.g. invoice ID appears as a quoted field, not buried in a markdown table), and large results are truncated with an explicit count of omitted records
**Plans**: 3 plans
  - [x] 05-01-PLAN.md — Wave 0: contract test scaffold for QUAL-01, QUAL-02, QUAL-03 (RED until implementation)
  - [x] 05-02-PLAN.md — Wave 1: rewrite all 24 tool descriptions + Annotated parameter annotations in server.py
  - [x] 05-03-PLAN.md — Wave 2: add ID exposure + standardize truncation to 20 in 5 tool modules

### Phase 6: Tool Consolidation
**Goal**: The tool surface shrinks to 14-16 dedicated tools through merging near-duplicates, dead routing code is deleted, and the dependency list reflects only what is actually used
**Depends on**: Phase 5
**Requirements**: CONS-01, CONS-02, CONS-03
**Success Criteria** (what must be TRUE):
  1. The MCP tool list exposed to clients contains 14-16 tools (down from 24) — audited list+get near-duplicate pairs are merged under a single tool with a `mode` or `action` parameter
  2. `src/routing/` directory is deleted; `date_parser.py` lives at `src/utils/date_parser.py` and is imported from there by any tool handler that accepts date phrases
  3. `rapidfuzz` is either removed from `pyproject.toml` (if no remaining caller) or its direct usage in a tool handler is documented — no orphan dependency exists
**Plans**: TBD

## Progress

**Execution Order:** Phases execute in numeric order: 3 → 4 → 5 → 6

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. HTTP Transport | v1.0 | — | Complete | 2026-04-02 |
| 2. Security Hardening | v1.0 | — | Complete | 2026-04-02 |
| 3. SDK Foundation | v1.1 | 0/2 | Planned | - |
| 4. Tool Interface Migration | v1.1 | 3/3 | Complete   | 2026-04-10 |
| 5. Tool Quality | v1.1 | 0/3 | Planned | - |
| 6. Tool Consolidation | v1.1 | 0/TBD | Not started | - |
