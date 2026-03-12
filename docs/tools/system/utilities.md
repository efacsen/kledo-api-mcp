# System Utility Tools

Utility tools for managing the Kledo MCP Server. These tools help with cache management and connection testing.

## utility_cache

Manage the server cache. Use the `action` parameter to clear the cache or retrieve statistics.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| action | string | **Yes** | Cache operation: `"clear"` or `"stats"` |

### Example — Clear Cache

**Request:**
```json
{
  "action": "clear"
}
```

**Response:** Returns confirmation message with number of cache entries cleared.

### Example — Cache Stats

**Request:**
```json
{
  "action": "stats"
}
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
