"""
Utility tools for Kledo MCP Server
"""
from typing import Any, Dict
from mcp.types import Tool

from ..kledo_client import KledoAPIClient


def get_tools() -> list[Tool]:
    """Get list of utility tools."""
    return [
        Tool(
            name="utility_clear_cache",
            description="Clear all cached data and force fresh data retrieval on next requests.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="utility_get_cache_stats",
            description="Get cache statistics including hit rate, size, and performance metrics.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="utility_test_connection",
            description="Test connection to Kledo API and verify authentication status.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:
    """Handle utility tool calls."""
    if name == "utility_clear_cache":
        return await _clear_cache(arguments, client)
    elif name == "utility_get_cache_stats":
        return await _get_cache_stats(arguments, client)
    elif name == "utility_test_connection":
        return await _test_connection(arguments, client)
    else:
        return f"Unknown utility tool: {name}"


async def _clear_cache(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Clear cache."""
    try:
        if client.cache:
            count = client.cache.clear()
            return f"Cache cleared successfully. Removed {count} cached entries."
        else:
            return "Cache is not enabled."
    except Exception as e:
        return f"Error clearing cache: {str(e)}"


async def _get_cache_stats(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get cache statistics."""
    try:
        if not client.cache:
            return "Cache is not enabled."

        stats = client.cache.get_stats()

        result = ["# Cache Statistics\n"]

        result.append(f"**Status**: {'Enabled' if stats['enabled'] else 'Disabled'}")
        result.append(f"**Current Size**: {stats['size']} / {stats['max_size']} entries")
        result.append(f"**Hit Rate**: {stats['hit_rate']}")
        result.append(f"**Total Hits**: {stats['hits']}")
        result.append(f"**Total Misses**: {stats['misses']}")
        result.append(f"**Total Requests**: {stats['total_requests']}")
        result.append(f"**Cache Sets**: {stats['sets']}")
        result.append(f"**Evictions**: {stats['evictions']}")
        result.append(f"**Expirations**: {stats['expirations']}")

        # Performance assessment
        hit_rate_value = float(stats['hit_rate'].rstrip('%'))

        performance = ""
        if hit_rate_value >= 80:
            performance = "Excellent - Cache is working very effectively"
        elif hit_rate_value >= 60:
            performance = "Good - Cache is providing significant benefit"
        elif hit_rate_value >= 40:
            performance = "Fair - Consider adjusting TTL settings"
        else:
            performance = "Poor - Cache may need optimization"

        result.append(f"\n**Performance**: {performance}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching cache stats: {str(e)}"


async def _test_connection(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Test API connection."""
    try:
        result = ["# Connection Test\n"]

        # Check authentication status
        is_auth = client.auth.is_authenticated
        result.append(f"**Authentication Status**: {'✓ Authenticated' if is_auth else '✗ Not Authenticated'}")

        if is_auth:
            result.append(f"**Access Token**: Present")
            result.append(f"**Token Expiry**: {client.auth._token_expiry}")

        # Try a simple API call
        result.append("\n**Testing API Connection...**")

        try:
            # Test with a lightweight endpoint
            test_data = await client.get_raw("/banks", cache_category="config")

            if test_data:
                result.append("✓ API Connection Successful")
                result.append("\n**Server**: Kledo API")
                result.append(f"**Base URL**: {client.auth.base_url}")
            else:
                result.append("✗ API returned empty response")

        except Exception as api_error:
            result.append(f"✗ API Connection Failed: {str(api_error)}")

        return "\n".join(result)

    except Exception as e:
        return f"Error testing connection: {str(e)}"
