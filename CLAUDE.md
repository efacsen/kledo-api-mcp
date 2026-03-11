# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kledo MCP Server — a Python MCP (Model Context Protocol) server that bridges Claude AI with the Kledo accounting software REST API. It exposes 24 read-only tools across 10 categories (revenue, invoices, products, contacts, orders, deliveries, sales analytics, financial, analytics/commission, utilities) to Claude Desktop and other MCP clients via stdio transport. Built for a paint distribution company with bilingual (Indonesian/English) support.

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
pytest tests/                              # Run all tests (80% coverage enforced)
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

1. **MCP Transport** (`src/server.py`) — Registers tools, dispatches `call_tool()` by tool name prefix to the appropriate handler module. Uses stdio transport via `mcp.server.stdio`.

2. **Tool Handlers** (`src/tools/*.py`) — Each module exports `get_tools() -> list[Tool]` and `async handle_tool(name, arguments, client) -> str`. Modules: `financial`, `invoices`, `revenue`, `sales_analytics`, `orders`, `contacts`, `deliveries`, `products`, `utilities`.

3. **Smart Routing** (`src/routing/`) — Natural language query routing using fuzzy matching (RapidFuzz at 80% threshold), synonym mapping for ID/EN business terms, idiomatic pattern matching, and relevance scoring.

4. **API Client** (`src/kledo_client.py`) — Async HTTP client (httpx) with cache-aware GET requests. Endpoints loaded from `config/endpoints.yaml` (80+ endpoints).

5. **Cache** (`src/cache.py`) — In-memory TTL-based cache. TTLs configured per category in `config/cache_config.yaml` (e.g., invoices: 60s, products: 3600s, contacts: 1800s).

6. **Auth** (`src/auth.py`) — Supports API key (recommended) or email/password with automatic token refresh.

7. **Domain Models** (`src/entities/models/`) — Pydantic models for Invoice, Contact, Product, Order, Delivery, Account. Field mapping from Kledo API fields in `src/mappers/kledo_mapper.py`.

### Key Patterns

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
