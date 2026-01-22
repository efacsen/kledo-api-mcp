# System Utility Tools

Utility tools for managing the Kledo MCP Server. These tools help with cache management and connection testing.

## utility_clear_cache

Clear all cached data and force fresh data retrieval on next requests.

### Parameters

This tool takes no parameters.

### Example

**Request:**
```json
{}
```

**Response:** Returns confirmation message with number of cache entries cleared.

---

## utility_get_cache_stats

Get cache statistics including hit rate, size, and performance metrics.

### Parameters

This tool takes no parameters.

### Example

**Request:**
```json
{}
```

**Response:** Returns cache statistics including:
- Status (enabled/disabled)
- Current size vs. max size
- Hit rate percentage
- Total hits and misses
- Total requests
- Cache sets count
- Evictions and expirations
- Performance assessment

---

## utility_test_connection

Test connection to Kledo API and verify authentication status.

### Parameters

This tool takes no parameters.

### Example

**Request:**
```json
{}
```

**Response:** Returns connection test results including:
- Authentication status
- Access token presence
- Token expiry
- API connection test result
- Base URL

---

## See Also

- [Tool Catalog](../index.md) - All available tools
