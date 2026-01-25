# Codebase Structure

**Analysis Date:** 2026-01-21

## Directory Layout

```
kledo-api-mcp/
├── .planning/               # GSD planning documents
├── config/                  # YAML configuration files
│   ├── cache_config.yaml    # Cache TTL tier configuration
│   └── endpoints.yaml       # Kledo API endpoint mapping
├── src/                     # Main source code
│   ├── __init__.py
│   ├── server.py            # MCP server entry point
│   ├── auth.py              # Authentication handler
│   ├── cache.py             # Caching mechanism
│   ├── kledo_client.py      # Kledo API client
│   ├── models/              # Data models (placeholder directory)
│   ├── tools/               # Tool implementations by domain
│   │   ├── __init__.py
│   │   ├── financial.py     # Financial reports
│   │   ├── invoices.py      # Invoice operations
│   │   ├── orders.py        # Order operations
│   │   ├── products.py      # Product catalog
│   │   ├── contacts.py      # Contact/CRM operations
│   │   ├── deliveries.py    # Delivery/shipping
│   │   └── utilities.py     # Server utilities
│   └── utils/               # Shared utilities
│       ├── __init__.py
│       ├── helpers.py       # Helper functions
│       └── logger.py        # Logging configuration
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_auth.py
│   ├── test_cache.py
│   ├── test_kledo_client.py
│   ├── test_server.py
│   ├── test_tools_*.py      # Tests for each tool module
├── .env.example             # Environment variable template
├── .gitignore
├── requirements.txt         # Python dependencies
└── README.md
```

## Directory Purposes

**`src/`:**
- Purpose: All application source code and business logic
- Contains: Server initialization, API client, authentication, tool handlers, utilities
- Key files: `server.py` (entry point), `kledo_client.py` (API layer), auth and cache infrastructure

**`src/tools/`:**
- Purpose: Tool implementations organized by business domain
- Contains: 7 modules corresponding to Kledo API functional areas
- Key files: Each module (invoices, orders, products, contacts, deliveries, financial, utilities) provides get_tools() and handle_tool()

**`src/utils/`:**
- Purpose: Reusable helper functions and cross-cutting concerns
- Contains: Date/currency formatting, parameter cleaning, hashing, logging setup
- Key files: `helpers.py` (formatting/parsing), `logger.py` (loguru configuration)

**`config/`:**
- Purpose: External configuration files loaded at runtime
- Contains: YAML files for endpoint mapping and cache tier settings
- Key files: `endpoints.yaml` (API path mapping), `cache_config.yaml` (TTL configuration)

**`tests/`:**
- Purpose: Full test suite with unit and integration tests
- Contains: Test files matching each source module
- Key files: `conftest.py` (pytest fixtures), `test_*.py` files for each module

**`.planning/codebase/`:**
- Purpose: GSD documentation artifacts
- Contains: Architecture analysis, structure guide, conventions, testing patterns, concerns
- Generated: Yes (by GSD mapper)
- Committed: Yes

## Key File Locations

**Entry Points:**
- `src/server.py` (lines 173-180): Main async function that creates and runs KledoMCPServer
- `src/server.py` method `list_tools()`: Returns all available tools to Claude
- `src/server.py` method `call_tool()`: Routes tool execution to appropriate handler

**Configuration:**
- `config/endpoints.yaml`: Maps category/name pairs to API endpoint paths (e.g., "invoices.list" → "/finance/invoices")
- `config/cache_config.yaml`: Defines TTL tiers for different data types (master_data, transactional, analytical, realtime)
- `.env.example`: Template showing required environment variables (KLEDO_EMAIL, KLEDO_PASSWORD, KLEDO_BASE_URL, etc.)

**Core Logic:**
- `src/auth.py`: KledoAuthenticator class managing token lifecycle and header generation
- `src/kledo_client.py`: KledoAPIClient class wrapping HTTP requests with caching and endpoint resolution
- `src/cache.py`: KledoCache class with TTL-based in-memory storage
- `src/server.py`: KledoMCPServer class coordinating tool registration and execution

**Business Domain Tools:**
- `src/tools/invoices.py`: Sales/purchase invoice listing, detail, totals (invoice_* tools)
- `src/tools/orders.py`: Sales/purchase order operations (order_* tools)
- `src/tools/products.py`: Product catalog queries (product_* tools)
- `src/tools/contacts.py`: Customer/vendor information (contact_* tools)
- `src/tools/deliveries.py`: Shipment tracking (delivery_* tools)
- `src/tools/financial.py`: Financial reports and analytics (financial_* tools)
- `src/tools/utilities.py`: Server diagnostics and utilities (utility_* tools)

**Testing:**
- `tests/conftest.py`: Pytest fixtures and mocks
- `tests/test_auth.py`: Authentication flow tests
- `tests/test_cache.py`: Cache behavior tests
- `tests/test_kledo_client.py`: API client tests
- `tests/test_server.py`: MCP server tests
- `tests/test_tools_*.py`: Individual tool handler tests (6 files)

## Naming Conventions

**Files:**
- Python modules: snake_case (e.g., `kledo_client.py`, `cache.py`)
- Config files: snake_case with .yaml (e.g., `cache_config.yaml`)
- Test files: `test_*.py` format matching source module name

**Directories:**
- Package directories: snake_case lowercase (e.g., `tools`, `utils`, `models`)
- Config directory: lowercase `config`
- Test directory: lowercase `tests`

**Functions:**
- Public functions: snake_case (e.g., `list_invoices()`, `ensure_authenticated()`)
- Private functions: Leading underscore in tools and handlers (e.g., `_list_sales_invoices()`, `_request()`)
- Tool definitions: Exported from get_tools(), used via handle_tool()

**Classes:**
- PascalCase for all classes (e.g., `KledoMCPServer`, `KledoAPIClient`, `KledoAuthenticator`, `KledoCache`)

**Tool Names:**
- Pattern: `{domain}_{operation}` (e.g., `invoice_list_sales`, `order_get_detail`, `product_search`)
- Domains: financial, invoice, order, product, contact, delivery, utility
- Operations: list, get_detail, get_totals, search, etc.

**Environment Variables:**
- Uppercase with underscores: `KLEDO_EMAIL`, `KLEDO_PASSWORD`, `KLEDO_BASE_URL`, `KLEDO_APP_CLIENT`, `MCP_SERVER_NAME`, `CACHE_ENABLED`, `LOG_LEVEL`, `LOG_FILE`

## Where to Add New Code

**New Feature (new API integration):**
- Primary code: Create new module in `src/tools/{feature}.py` following the pattern:
  ```python
  def get_tools() -> list[Tool]:
      return [Tool(name="...", description="...", inputSchema={...})]

  async def handle_tool(name: str, arguments: Dict, client: KledoAPIClient) -> str:
      if name == "...":
          return await _implementation(arguments, client)
  ```
- Tests: Add `tests/test_tools_{feature}.py`
- Integration: Add module to `src/tools/__init__.py` imports and `src/server.py` list_tools() aggregation (line 95-113)

**New Endpoint Access:**
- Update `config/endpoints.yaml` to add category and endpoint mapping
- Use `client.get(category, name, params, path_params)` in handlers
- Or use `client.get_raw(endpoint, params)` for unmapped endpoints

**New Utility Function:**
- Add to `src/utils/helpers.py` if general-purpose (formatting, parsing, data manipulation)
- Import in handlers with `from ..utils.helpers import function_name`

**New Data Model:**
- Location: `src/models/` (currently placeholder, extend as needed)
- Pattern: Use type hints in function signatures rather than separate model classes currently

**New Configuration:**
- If runtime configuration needed: Add YAML file to `config/` directory
- If environment-driven: Add to `.env.example` and load in `src/server.py` via `os.getenv()`

## Special Directories

**`src/models/`:**
- Purpose: Reserved for data models/schemas
- Generated: No
- Committed: Yes
- Current state: Placeholder directory, models use inline type hints instead

**`config/`:**
- Purpose: Runtime configuration files in YAML
- Generated: No (hand-written, committed to repo)
- Committed: Yes
- Loaded by: `KledoAPIClient._load_endpoints_config()` and `KledoCache.__init__()`

**`tests/`:**
- Purpose: Full test coverage with unit and integration tests
- Generated: No (hand-written)
- Committed: Yes
- Run via: pytest from project root

**`.planning/codebase/`:**
- Purpose: GSD-generated documentation and analysis
- Generated: Yes (by /gsd:map-codebase command)
- Committed: Yes
- Contents: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md

**`venv/`:**
- Purpose: Python virtual environment
- Generated: Yes
- Committed: No (in .gitignore)

**`.claude/`:**
- Purpose: Claude workspace settings
- Generated: Yes
- Committed: No

---

*Structure analysis: 2026-01-21*
