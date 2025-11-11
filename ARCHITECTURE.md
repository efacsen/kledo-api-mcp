# Kledo MCP Server - Architecture Documentation

## Overview

The Kledo MCP Server is designed to provide AI agents with secure, efficient access to Kledo CRM data through the Model Context Protocol. The architecture prioritizes read-only operations, intelligent caching, and maintainability.

## Design Principles

### 1. Separation of Concerns
- **MCP Layer**: Protocol handling and tool registration
- **Business Logic**: Tool handlers with domain-specific logic
- **API Client**: HTTP communication and caching
- **Authentication**: Token management and refresh

### 2. Read-Only by Design
- All operations are GET requests
- No write, update, or delete capabilities (Phase 1)
- Protects against accidental data modification

### 3. Intelligent Caching
- Multi-tier caching strategy based on data volatility
- Configurable TTLs per data category
- Manual cache invalidation when needed

### 4. Extensibility
- Modular tool structure for easy addition of new features
- Configuration-driven endpoint management
- Plugin-style tool registration

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AI Agent                             │
│                    (Claude Desktop)                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ MCP Protocol (stdio)
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    MCP Server (server.py)                   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │          Tool Registry & Router                     │   │
│  │  - list_tools()                                     │   │
│  │  - call_tool(name, args)                           │   │
│  └──────────────────┬──────────────────────────────────┘   │
└─────────────────────┼──────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐         ┌────────▼────────┐
│  Tool Handlers  │         │   Utilities     │
│                 │         │                 │
│ • financial     │         │ • logger        │
│ • invoices      │         │ • helpers       │
│ • orders        │         │ • validators    │
│ • products      │         │                 │
│ • contacts      │         └─────────────────┘
│ • deliveries    │
└───────┬─────────┘
        │
┌───────▼──────────────────────────────────────────────────┐
│              Kledo API Client (kledo_client.py)          │
│                                                           │
│  ┌────────────────┐         ┌──────────────────┐        │
│  │  Request Mgmt  │────────▶│  Cache Manager   │        │
│  │  - get()       │         │  - get()         │        │
│  │  - get_raw()   │         │  - set()         │        │
│  │  - _request()  │         │  - clear()       │        │
│  └────────┬───────┘         └──────────────────┘        │
└───────────┼──────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────┐
│         Authentication Layer (auth.py)                    │
│                                                           │
│  ┌─────────────────────────────────────────────┐        │
│  │  Token Manager                               │        │
│  │  - login()                                   │        │
│  │  - ensure_authenticated()                    │        │
│  │  - get_auth_headers()                        │        │
│  │  - Token expiry tracking                     │        │
│  └─────────────────────────────────────────────┘        │
└───────────┼──────────────────────────────────────────────┘
            │ HTTPS (Bearer Token)
            │
┌───────────▼──────────────────────────────────────────────┐
│                   Kledo REST API                          │
│              (api.kledo.com/api/v1)                       │
└───────────────────────────────────────────────────────────┘
```

## Data Flow

### Typical Request Flow

1. **User Query**: AI agent receives natural language query
2. **Tool Selection**: Agent selects appropriate MCP tool
3. **Tool Invocation**: MCP server routes to tool handler
4. **Cache Check**: Client checks cache for existing data
5. **API Request** (if cache miss):
   - Ensure authentication is valid
   - Build request with parameters
   - Execute HTTP request
   - Handle response/errors
6. **Cache Store**: Store successful response
7. **Format Response**: Tool formats data for display
8. **Return to Agent**: Formatted text returned to AI

### Authentication Flow

```
┌─────────┐
│ Server  │
│ Start   │
└────┬────┘
     │
     ▼
┌────────────────┐
│  Load Config   │
│  & Credentials │
└────┬───────────┘
     │
     ▼
┌────────────────────┐
│  Perform Login     │
│  POST /auth/login  │
└────┬───────────────┘
     │
     ▼
┌──────────────────────┐
│  Store Access Token  │
│  & Expiry Time       │
└────┬─────────────────┘
     │
     ▼
┌───────────────────────┐
│  Ready for Requests   │
└───────┬───────────────┘
        │
        ▼
   ┌──────────────┐      YES    ┌─────────────┐
   │ Token Valid? │─────────────▶│ Make Request│
   └───────┬──────┘              └─────────────┘
           │ NO
           ▼
   ┌──────────────┐
   │  Re-login    │
   └──────────────┘
```

## Caching Strategy

### Cache Tiers

#### Tier 1: Master Data (Slow-changing)
- **Products**: 2 hours
- **Contacts**: 2 hours
- **Accounts**: 4 hours
- **Configuration**: 8 hours

**Rationale**: Master data changes infrequently, so longer cache reduces API load.

#### Tier 2: Transactional (Moderate)
- **Invoices**: 30 minutes
- **Orders**: 30 minutes
- **Expenses**: 30 minutes

**Rationale**: Balance between freshness and performance for operational data.

#### Tier 3: Analytical (Expensive queries)
- **Reports**: 1 hour
- **Summaries**: 30 minutes
- **Dashboard**: 1 hour

**Rationale**: Complex aggregations are expensive; cache longer for performance.

#### Tier 4: Real-time (Critical)
- **Bank Balances**: 5 minutes
- **Stock Levels**: 10 minutes

**Rationale**: Financial data needs to be relatively fresh.

### Cache Implementation

```python
class CacheEntry:
    - value: Any
    - created_at: timestamp
    - ttl: seconds
    - hits: count
    - is_expired: bool

class KledoCache:
    - _cache: Dict[key, CacheEntry]
    - get(key) → value | None
    - set(key, value, category, ttl)
    - clear() → count
    - get_stats() → stats dict
```

### Cache Key Format

```
{endpoint}:{param_hash}
```

Examples:
- `/finance/invoices:a1b2c3d4` (invoice list with specific params)
- `/finance/products:e5f6g7h8` (product search)
- `/reports/activity-team:` (no params)

## Tool Organization

### Tool Categories

Each tool category is a separate module under `src/tools/`:

```python
# Tool module structure
def get_tools() -> list[Tool]:
    """Return list of MCP Tool definitions"""
    return [Tool(...), Tool(...)]

async def handle_tool(name: str, args: Dict, client: KledoAPIClient) -> str:
    """Route tool calls to appropriate handlers"""
    if name == "tool_name":
        return await _handler_function(args, client)
```

### Tool Naming Convention

Format: `{category}_{action}_{target}`

Examples:
- `financial_sales_summary`
- `invoice_list_sales`
- `product_search_by_sku`
- `delivery_get_pending`

### Tool Response Format

All tools return markdown-formatted text:

```markdown
# Title

**Metadata Fields**: values

## Section Header

- List items
- More items

### Subsection

Detailed information...
```

## Error Handling

### Error Types

1. **Authentication Errors**
   - Invalid credentials → Re-authenticate
   - Expired token → Automatic refresh
   - Network errors → Retry with backoff

2. **API Errors**
   - 4xx Client errors → Return error message to user
   - 5xx Server errors → Log and return friendly message
   - Timeout → Return timeout message

3. **Data Errors**
   - Empty results → "No data found" message
   - Malformed data → Log warning, return partial data
   - Missing fields → Use safe_get() with defaults

### Error Response Pattern

```python
try:
    # Perform operation
    data = await client.get(...)
    return format_response(data)
except httpx.HTTPStatusError as e:
    logger.error(f"HTTP error: {e}")
    return f"Error: {e.response.status_code}"
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return f"Error: {str(e)}"
```

## Configuration Management

### Configuration Files

1. **`config/endpoints.yaml`**
   - Maps friendly names to API endpoints
   - Organizes endpoints by category
   - Documents query parameters

2. **`config/cache_config.yaml`**
   - Defines TTL for each data category
   - Cache size limits
   - Cleanup intervals

3. **`.env`**
   - Credentials (never committed)
   - Runtime settings
   - Feature flags

### Loading Configuration

```python
# Lazy loading on first use
if not self._endpoints:
    self._load_endpoints_config(config_path)

# YAML parsing
with open(path, 'r') as f:
    config = yaml.safe_load(f)
```

## Security Considerations

### Credential Management
- Credentials stored in `.env` (gitignored)
- Never logged or exposed in errors
- Use dedicated read-only account

### API Access
- HTTPS only communication
- Bearer token authentication
- Automatic token refresh
- Request timeout limits

### Data Exposure
- Read-only access prevents modifications
- No sensitive data in cache keys
- Logs scrubbed of PII
- Cache cleared on logout

## Performance Optimization

### Strategies

1. **Caching** - Primary optimization
2. **Pagination** - Limit result sets (default 50)
3. **Selective fields** - Only request needed data
4. **Async I/O** - Non-blocking requests
5. **Connection pooling** - Reuse HTTP connections

### Monitoring

Track these metrics:
- Cache hit rate (target: >70%)
- Average response time
- API error rate
- Authentication failures

Access via: `utility_get_cache_stats` tool

## Testing Strategy

### Unit Tests
- Test each tool handler in isolation
- Mock API responses
- Verify error handling

### Integration Tests
- Test with actual API (sandbox)
- Verify authentication flow
- Test cache behavior

### Manual Testing
- Use Claude Desktop for real queries
- Test natural language understanding
- Verify output formatting

## Future Enhancements

### Phase 2: Write Operations
- Add POST/PUT/DELETE tools
- Require explicit user confirmation
- Transaction rollback capability
- Audit logging

### Phase 3: Advanced Features
- Webhook support for real-time updates
- GraphQL alternative API
- Bulk operations
- Advanced reporting/analytics

### Phase 4: Multi-tenancy
- Support multiple Kledo accounts
- Per-account caching
- Credential management UI

## Deployment Considerations

### Local Development
- Run directly with `python -m src.server`
- Use `.env` for configuration
- Logs to stdout and file

### Production Deployment
- Consider using Docker
- Environment-based configuration
- Centralized logging (e.g., Sentry)
- Health check endpoint

### Monitoring
- Track API usage and quotas
- Monitor error rates
- Alert on authentication failures
- Cache performance metrics

## Dependencies

### Core
- `mcp` - Model Context Protocol SDK
- `httpx` - Async HTTP client
- `pydantic` - Data validation
- `python-dotenv` - Environment management

### Supporting
- `pyyaml` - Configuration parsing
- `loguru` - Structured logging
- `python-dateutil` - Date handling

### Development
- `pytest` - Testing framework
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking

---

**Last Updated**: 2025-01-11
**Version**: 1.0.0
