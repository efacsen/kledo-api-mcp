# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kledo MCP Server — a Python MCP (Model Context Protocol) server that bridges Claude AI with the Kledo accounting software REST API. It exposes 24 read-only tools across 10 categories (revenue, invoices, products, contacts, orders, deliveries, sales analytics, financial, analytics/commission, utilities) to Claude Desktop and other MCP clients via stdio transport. Built for a paint distribution company with bilingual (Indonesian/English) support.

## Active Development Direction

This server is being modernized from the pre-1.0 MCP SDK pattern to MCP 1.x best practices.
The full audit and migration plan is in `MCP_MODERNIZATION.md`. Key decisions already made:

- **Target SDK**: `mcp>=1.0.0` with `FastMCP` (`mcp.server.fastmcp`) — replaces the raw `Server` class
- **Tool count target**: 8–10 promoted dedicated tools + `search_tools`/`run_tool` catalog pair for the long tail
- **`src/routing/`**: Currently dead code (never called by server.py). Will be wired into the `search_tools` catalog tool. Only `date_parser.py` should be kept standalone (move to `src/utils/`).
- **All tools are read-only**: Every tool must have `annotations={"readOnlyHint": True, "openWorldHint": True}`
- **Error returns**: Must use `{"isError": True, "content": [...]}` — not plain TextContent
- **Progress reporting**: `commission`, `analytics`, and `revenue` tools must use `ctx.report_progress()`

### Migration Phases (see MCP_MODERNIZATION.md for full detail)

| Phase | Scope | Status |
|---|---|---|
| 1 | Bump SDK, migrate server.py to FastMCP, add readOnlyHint, fix isError | TODO |
| 2 | Rewrite tool descriptions, add param descriptions, add progress reporting | TODO |
| 3 | Reduce tool count, wire routing into search_tools catalog | TODO |
| 4 | Remote HTTP transport (optional) | TODO |

### Do Not Regress

- `src/kledo_client.py`, `src/auth.py`, `src/cache.py` — well-built, do not refactor without reason
- `config/endpoints.yaml` — configuration-driven endpoints must stay, do not hardcode URLs
- Bilingual support (Indonesian/English) in tool descriptions and parameter handling

## Commands

### Install & Run
```bash
pip install -e .              # Install in editable mode
pip install -e ".[dev]"       # Install with dev dependencies
kledo-mcp                     # Start server (runs setup wizard on first run)
kledo-mcp --setup             # Re-run interactive setup wizard
kledo-mcp --test              # Test Kledo API connection
python -m src.server          # Run server directly
```

### Testing
```bash
pytest tests/                              # Run all tests (45% coverage enforced)
pytest tests/test_auth.py                  # Run a single test file
pytest tests/test_auth.py::test_login      # Run a single test function
pytest --no-cov tests/                     # Skip coverage reporting
```

### Code Quality
```bash
ruff check src/               # Lint
ruff check src/ --fix          # Lint with auto-fix
black src/                     # Format
mypy src/                      # Type check (strict mode)
```

### Documentation
```bash
mkdocs serve                   # Local docs preview
mkdocs build                   # Build static docs site
```

## Architecture

### Layer Stack (top → bottom)

1. **MCP Transport** (`src/server.py`) — Currently uses pre-1.0 `Server` class with `@server.list_tools()` / `@server.call_tool()` pattern. **Target: migrate to `FastMCP`** with decorator-based tools and lifespan hook for client init.

2. **Tool Handlers** (`src/tools/*.py`) — Each module exports `get_tools() -> list[Tool]` and `async handle_tool(name, arguments, client) -> str`. Modules: `analytics`, `commission`, `contacts`, `deliveries`, `financial`, `invoices`, `orders`, `products`, `revenue`, `sales_analytics`, `utilities`.

3. **Smart Routing** (`src/routing/`) — **Currently dead code — not called anywhere.** Contains fuzzy matching (RapidFuzz), synonym mapping (ID/EN), idiomatic patterns, relevance scoring. Target: wire into a `search_tools` catalog tool. `date_parser.py` should be moved to `src/utils/`.

4. **API Client** (`src/kledo_client.py`) — Async HTTP client (httpx) with cache-aware GET requests. Endpoints loaded from `config/endpoints.yaml` (80+ endpoints).

5. **Cache** (`src/cache.py`) — In-memory TTL-based cache. TTLs configured per category in `config/cache_config.yaml` (e.g., invoices: 60s, products: 3600s, contacts: 1800s).

6. **Auth** (`src/auth.py`) — Supports API key (recommended) or email/password with automatic token refresh.

7. **Domain Models** (`src/entities/models/`) — Pydantic models for Invoice, Contact, Product, Order, Delivery, Account. Field mapping from Kledo API fields in `src/mappers/kledo_mapper.py`.

### Key Patterns (current — pre-migration)

- **Tool dispatch**: `server.py` routes by tool name prefix (e.g., `revenue_` → `revenue.handle_tool()`, `invoice_` → `invoices.handle_tool()`).
- **Tool module interface**: Every tool module in `src/tools/` must expose `get_tools()` and `handle_tool()`. Internal operations are prefixed with underscore (e.g., `_list_products()`).
- **All async**: The entire call chain uses `async/await` — server, client, auth, tool handlers.
- **Configuration-driven endpoints**: API paths live in `config/endpoints.yaml`, not hardcoded.

## Domain-Specific Knowledge

- **Commission calculation** uses revenue BEFORE tax (`subtotal`) from PAID invoices only (`status_id=3`).
- **Status codes**: 1 = Belum Dibayar (Unpaid), 2 = Dibayar Sebagian (Partially Paid), 3 = Lunas (Paid).
- **Revenue formula**: `amount_after_tax = subtotal + total_tax`. Tools always show both before-tax and after-tax amounts.

## Code Conventions

- Python 3.11+. Type hints required on all function signatures (mypy strict).
- Black formatting at 100-char line length. Ruff linting with E/W/F/I/B/C4/UP rules.
- Loguru for logging (`from loguru import logger`). Structured messages with context.
- Relative imports within `src/` (e.g., `from ..kledo_client import KledoAPIClient`).
- Tests in `tests/` mirror source structure with `test_` prefix. Async tests use `pytest-asyncio` with `asyncio_mode = "auto"`.

## Configuration

- Environment variables via `.env` file (loaded with python-dotenv). Key vars: `KLEDO_API_KEY`, `KLEDO_BASE_URL`, `CACHE_ENABLED`, `LOG_LEVEL`.
- Config search order: env vars → `~/.kledo/.env` → `~/.config/kledo/.env` → `/etc/kledo/.env` → project `.env`.
