# Architecture

**Analysis Date:** 2026-01-21

## Pattern Overview

**Overall:** MCP (Model Context Protocol) Server with Tool-Based API Integration

**Key Characteristics:**
- Adapter pattern between Kledo REST API and Claude MCP interface
- Async/await concurrency model throughout
- Modular tool handlers organized by business domain
- Configuration-driven endpoint mapping
- Multi-tier caching strategy with TTL controls

## Layers

**Transport Layer (MCP/StdIO):**
- Purpose: Handles bidirectional communication with Claude client
- Location: `src/server.py` (lines 165-170)
- Contains: MCP server initialization, tool registration, request/response routing
- Depends on: mcp package, asyncio
- Used by: Main entry point to expose tools to Claude

**Authentication Layer:**
- Purpose: Manages Kledo API authentication and token lifecycle
- Location: `src/auth.py`
- Contains: Token acquisition, expiry tracking, token refresh logic
- Depends on: httpx (async HTTP client)
- Used by: API client for every request

**API Integration Layer:**
- Purpose: HTTP client for Kledo API with caching and request management
- Location: `src/kledo_client.py`
- Contains: HTTP request logic, endpoint configuration loading, cache integration
- Depends on: httpx, yaml, auth layer, cache layer
- Used by: All tool handlers

**Caching Layer:**
- Purpose: In-memory TTL-based cache for API responses
- Location: `src/cache.py`
- Contains: Cache entries with TTL expiry, statistics tracking, configuration loading
- Depends on: yaml (for configuration)
- Used by: API client to reduce redundant calls

**Business Logic Layer (Tool Handlers):**
- Purpose: Domain-specific tool implementations exposing Kledo functionality
- Location: `src/tools/` (7 modules: invoices, orders, products, contacts, deliveries, financial, utilities)
- Contains: Tool definition (name, description, schema) and execution logic
- Depends on: API client, helpers for formatting/parsing
- Used by: MCP server's call_tool handler

**Utilities Layer:**
- Purpose: Helper functions for common operations
- Location: `src/utils/helpers.py` and `src/utils/logger.py`
- Contains: Date parsing, currency formatting, parameter cleaning, hashing, logging setup
- Depends on: hashlib, json, datetime, loguru
- Used by: Tool handlers and API client

## Data Flow

**Tool Invocation Flow:**

1. Claude client sends tool request → MCP Server via StdIO
2. `KledoMCPServer.call_tool()` receives tool name and arguments (line 118-159)
3. Tool prefix determines handler module (financial_, invoice_, order_, etc.)
4. Handler module's `handle_tool()` function routes to specific implementation
5. Implementation parses arguments, calls API client methods
6. API client checks cache for GET requests
7. If cache miss, authenticator ensures valid token via `ensure_authenticated()`
8. HTTP request sent with auth headers to Kledo API endpoint
9. Response cached (if GET) and returned to handler
10. Handler formats result (text, table, or summary)
11. Result returned to MCP server as TextContent
12. Server returns to Claude client

**Authentication Flow:**

1. Server initialization calls `initialize_client()` (line 47-88 in server.py)
2. Creates KledoAuthenticator with email/password from environment
3. Calls `auth.login()` to get initial token and expiry time
4. Token stored in authenticator with expiry tracking
5. For subsequent requests, API client calls `auth.ensure_authenticated()`
6. If token valid, returns existing token in headers
7. If expired, automatically re-authenticates with stored credentials
8. Token refresh happens transparently to tool handlers

**Caching Strategy:**

1. Request arrives at API client's `_request()` method (line 91-171)
2. For GET requests, build cache key from endpoint + params hash
3. Check cache for existing entry with TTL validation
4. Cache hit: return cached data immediately (no API call)
5. Cache miss: execute HTTP request
6. On success, store response in cache with category-specific TTL
7. Cache TTL tiers defined in `config/cache_config.yaml`:
   - Master data (products, contacts): 2-8 hours
   - Transactional (invoices, orders): 15-30 minutes
   - Analytical (reports): 30-60 minutes
   - Real-time (balances, stock): 5-10 minutes

## Key Abstractions

**KledoMCPServer:**
- Purpose: Orchestrates MCP protocol, tool registration, and routing
- Examples: `src/server.py` lines 33-170
- Pattern: Singleton-like initialization with async context manager for server lifecycle

**KledoAPIClient:**
- Purpose: Unified API access with configuration-driven endpoints
- Examples: `src/kledo_client.py` lines 15-339
- Pattern: Uses endpoint configuration YAML to abstract API paths, provides convenience methods for common operations

**Tool Handlers (via handle_tool pattern):**
- Purpose: Domain-specific tool implementations following consistent interface
- Examples: `src/tools/invoices.py`, `src/tools/orders.py`, `src/tools/products.py`
- Pattern: Each module exports `get_tools()` (list of Tool objects) and `handle_tool(name, args, client)` (async execution)

**KledoAuthenticator:**
- Purpose: Token lifecycle management with automatic refresh
- Examples: `src/auth.py` lines 10-165
- Pattern: Properties for state (is_authenticated), methods for actions (login, logout, ensure_authenticated)

**KledoCache:**
- Purpose: TTL-based in-memory cache with statistics
- Examples: `src/cache.py` lines 46+
- Pattern: Configuration-driven TTL tiers, tracks cache hits/misses, auto-cleanup of stale entries

## Entry Points

**Server Process:**
- Location: `src/server.py` lines 173-180 (main function)
- Triggers: CLI execution `python -m src.server`
- Responsibilities: Create KledoMCPServer, initialize client, run async event loop

**Tool List Request:**
- Location: `src/server.py` method `list_tools()` (lines 90-116)
- Triggers: Claude client initializes connection and queries available tools
- Responsibilities: Aggregate all tools from 7 handler modules, return unified list

**Tool Execution Request:**
- Location: `src/server.py` method `call_tool()` (lines 118-159)
- Triggers: Claude client calls a specific tool with arguments
- Responsibilities: Route to handler module, execute logic, catch errors, return formatted result

## Error Handling

**Strategy:** Hierarchical error catching with logging at each layer

**Patterns:**

**HTTP Layer (API Client):**
- Catches `httpx.HTTPStatusError`, `httpx.RequestError`, generic `Exception`
- Logs error details with response text for debugging
- Re-raises to handler for user-facing error messages
- Example: `src/kledo_client.py` lines 162-171

**Authentication Layer:**
- Catches HTTP errors during login/logout
- Returns boolean success/failure instead of raising
- Example: `src/auth.py` lines 92-101

**Tool Handler Layer:**
- Wraps all business logic in try/except
- Catches errors from API client and returns error text
- Example: `src/tools/invoices.py` lines 143-160 (catch blocks not shown, but pattern in all handlers)

**Server Layer:**
- Wraps tool execution in try/except (line 156-159 in server.py)
- Returns error message as TextContent to prevent server crash
- Logs error context for debugging

## Cross-Cutting Concerns

**Logging:**
- Framework: loguru
- Setup: `src/utils/logger.py` with environment-driven configuration
- Format: Colored console output with timestamp, level, module, function, line number
- File output: Optional with rotation and compression
- Usage: Every significant operation logged (authentication, caching, API requests, errors)

**Validation:**
- Environment variables checked on startup (`src/server.py` lines 51-57)
- Parameter cleaning before API requests (`src/kledo_client.py` line 134)
- Date parsing with fallback to None for invalid input (`src/utils/helpers.py` lines 42-99)
- Type checking for cached values and API responses

**Authentication:**
- Bearer token in Authorization header
- App-client header for device type identification
- Token expiry tracking with automatic re-authentication
- Credentials from environment variables only (no hardcoding)

**Configuration Management:**
- Environment variables: Credentials, logging, cache settings
- YAML files: Endpoint mapping, cache TTL tiers
- Config loading on demand with error handling

---

*Architecture analysis: 2026-01-21*
