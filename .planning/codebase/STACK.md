# Technology Stack

**Analysis Date:** 2026-01-21

## Languages

**Primary:**
- Python 3.13 - Primary language for all backend services and MCP server implementation

## Runtime

**Environment:**
- Python 3.13.7
- Virtual environment: `venv/` (local development)

**Package Manager:**
- pip - Python package manager
- Lockfile: `requirements.txt` (present)

## Frameworks

**Core:**
- MCP (Model Context Protocol) - Core framework for building AI-accessible server (mcp>=0.9.0)
- python-dotenv - Environment variable management from `.env` files

**HTTP & API:**
- httpx>=0.25.0 - Async HTTP client for making requests to Kledo API

**Data Validation & Configuration:**
- pydantic>=2.0.0 - Data validation and settings management
- pydantic-settings>=2.0.0 - Settings management from environment variables
- PyYAML>=6.0.0 - YAML configuration file parsing (used for `config/endpoints.yaml` and `config/cache_config.yaml`)

**Logging:**
- loguru>=0.7.0 - Structured logging framework with file output support

**Utilities:**
- python-dateutil>=2.8.0 - Date and time parsing utilities

## Key Dependencies

**Critical:**
- mcp>=0.9.0 - Why it matters: Foundation for MCP server implementation that exposes tools to AI agents
- httpx>=0.25.0 - Why it matters: Async HTTP client for all Kledo API communication
- pydantic>=2.0.0 - Why it matters: Request/response validation and environment configuration

**Infrastructure:**
- loguru>=0.7.0 - Structured logging with console and file output
- PyYAML>=6.0.0 - Configuration management for endpoints and cache policies

## Configuration

**Environment:**
- `.env` file (copied from `.env.example`)
- Environment variables control:
  - Kledo API credentials: `KLEDO_EMAIL`, `KLEDO_PASSWORD`, `KLEDO_BASE_URL`, `KLEDO_APP_CLIENT`
  - Cache settings: `CACHE_ENABLED`, `CACHE_DEFAULT_TTL`
  - Logging: `LOG_LEVEL`, `LOG_FILE`
  - MCP Server: `MCP_SERVER_NAME`, `MCP_SERVER_VERSION`

**Build:**
- No build configuration needed - pure Python application

**Configuration Files:**
- `config/endpoints.yaml` - Maps endpoint names to Kledo API paths (auth, reports, invoices, products, contacts, deliveries, bank, accounts, supporting data)
- `config/cache_config.yaml` - Defines cache TTL tiers for different data types (master_data: 2-8 hours, transactional: 15-30 minutes, analytical: 1 hour, realtime: 5-10 minutes)

## Testing Stack

**Testing Framework:**
- pytest>=7.4.0 - Test framework
- pytest-asyncio>=0.21.0 - Support for async test functions
- pytest-cov>=4.1.0 - Code coverage measurement

**Development Tools:**
- black>=23.0.0 - Code formatter (Python)
- ruff>=0.1.0 - Fast Python linter and formatter
- mypy>=1.5.0 - Static type checker

## Platform Requirements

**Development:**
- Python 3.10 or higher (Python 3.13.7 currently used)
- Virtual environment for dependency isolation
- macOS/Linux/Windows with Python environment

**Production:**
- Deployment target: Runs as standalone Python process
- Can be integrated into Claude Desktop via MCP server configuration
- Requires network access to Kledo API (https://api.kledo.com/api/v1)
- Requires valid Kledo credentials for authentication

---

*Stack analysis: 2026-01-21*
