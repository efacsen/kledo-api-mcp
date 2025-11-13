"""
Tests for utility tools
"""
import pytest
from unittest.mock import AsyncMock, Mock
from mcp.types import Tool

from src.tools import utilities
from src.kledo_client import KledoAPIClient
from src.cache import KledoCache


class TestUtilityTools:
    """Test suite for utility tools."""

    def test_get_tools(self):
        """Test get_tools returns correct tool definitions."""
        tools = utilities.get_tools()

        assert len(tools) == 3
        assert all(isinstance(tool, Tool) for tool in tools)

        tool_names = [tool.name for tool in tools]
        assert "utility_clear_cache" in tool_names
        assert "utility_get_cache_stats" in tool_names
        assert "utility_test_connection" in tool_names

    def test_tool_schemas(self):
        """Test that all tools have proper input schemas."""
        tools = utilities.get_tools()

        for tool in tools:
            assert "type" in tool.inputSchema
            assert "properties" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    @pytest.mark.asyncio
    async def test_handle_tool_clear_cache(self):
        """Test handle_tool routes utility_clear_cache correctly."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.clear = Mock(return_value=15)

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities.handle_tool(
            "utility_clear_cache",
            {},
            mock_client
        )

        assert "Cache cleared successfully" in result
        assert "15" in result
        mock_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_tool_clear_cache_disabled(self):
        """Test clear cache when cache is disabled."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = None

        result = await utilities.handle_tool(
            "utility_clear_cache",
            {},
            mock_client
        )

        assert "Cache is not enabled" in result

    @pytest.mark.asyncio
    async def test_handle_tool_get_cache_stats(self):
        """Test handle_tool routes utility_get_cache_stats correctly."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.get_stats = Mock(return_value={
            "enabled": True,
            "size": 50,
            "max_size": 1000,
            "hits": 200,
            "misses": 50,
            "hit_rate": "80.00%",
            "sets": 50,
            "evictions": 5,
            "expirations": 10,
            "total_requests": 250
        })

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities.handle_tool(
            "utility_get_cache_stats",
            {},
            mock_client
        )

        assert "Cache Statistics" in result
        assert "80.00%" in result
        assert "Enabled" in result
        assert "50 / 1000" in result

    @pytest.mark.asyncio
    async def test_handle_tool_get_cache_stats_disabled(self):
        """Test get cache stats when cache is disabled."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = None

        result = await utilities.handle_tool(
            "utility_get_cache_stats",
            {},
            mock_client
        )

        assert "Cache is not enabled" in result

    @pytest.mark.asyncio
    async def test_handle_tool_test_connection(self):
        """Test handle_tool routes utility_test_connection correctly."""
        mock_auth = Mock()
        mock_auth.is_authenticated = True
        mock_auth._token_expiry = "2024-12-31 23:59:59"
        mock_auth.base_url = "https://api.kledo.com/api/v1"

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.auth = mock_auth
        mock_client.get_raw = AsyncMock(return_value={"data": {"data": []}})

        result = await utilities.handle_tool(
            "utility_test_connection",
            {},
            mock_client
        )

        assert "Connection Test" in result
        assert "Authenticated" in result
        assert "API Connection Successful" in result

    @pytest.mark.asyncio
    async def test_handle_tool_test_connection_not_authenticated(self):
        """Test connection test when not authenticated."""
        mock_auth = Mock()
        mock_auth.is_authenticated = False

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.auth = mock_auth
        mock_client.get_raw = AsyncMock(return_value={"data": {"data": []}})

        result = await utilities.handle_tool(
            "utility_test_connection",
            {},
            mock_client
        )

        assert "Not Authenticated" in result

    @pytest.mark.asyncio
    async def test_handle_tool_test_connection_api_failure(self):
        """Test connection test when API call fails."""
        mock_auth = Mock()
        mock_auth.is_authenticated = True
        mock_auth._token_expiry = "2024-12-31"
        mock_auth.base_url = "https://api.kledo.com"

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.auth = mock_auth
        mock_client.get_raw = AsyncMock(side_effect=Exception("Network timeout"))

        result = await utilities.handle_tool(
            "utility_test_connection",
            {},
            mock_client
        )

        assert "API Connection Failed" in result
        assert "Network timeout" in result

    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self):
        """Test handle_tool with unknown tool name."""
        mock_client = Mock(spec=KledoAPIClient)

        result = await utilities.handle_tool(
            "utility_unknown_tool",
            {},
            mock_client
        )

        assert "Unknown utility tool" in result

    @pytest.mark.asyncio
    async def test_clear_cache_error_handling(self):
        """Test error handling in clear cache."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.clear = Mock(side_effect=Exception("Clear failed"))

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities.handle_tool(
            "utility_clear_cache",
            {},
            mock_client
        )

        assert "Error clearing cache" in result

    @pytest.mark.asyncio
    async def test_get_cache_stats_error_handling(self):
        """Test error handling in get cache stats."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.get_stats = Mock(side_effect=Exception("Stats error"))

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities.handle_tool(
            "utility_get_cache_stats",
            {},
            mock_client
        )

        assert "Error fetching cache stats" in result

    @pytest.mark.asyncio
    async def test_test_connection_error_handling(self):
        """Test error handling in test connection."""
        mock_auth = Mock()
        mock_auth.is_authenticated = True
        mock_auth._token_expiry = "2024-12-31"
        mock_auth.base_url = "https://api.kledo.com"

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.auth = mock_auth
        mock_client.get_raw = AsyncMock(side_effect=Exception("Unexpected error"))

        result = await utilities.handle_tool(
            "utility_test_connection",
            {},
            mock_client
        )

        assert "API Connection Failed" in result

    @pytest.mark.asyncio
    async def test_cache_stats_performance_assessment_excellent(self):
        """Test cache stats shows excellent performance."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.get_stats = Mock(return_value={
            "enabled": True, "size": 100, "max_size": 1000,
            "hits": 900, "misses": 100, "hit_rate": "90.00%",
            "sets": 100, "evictions": 0, "expirations": 0, "total_requests": 1000
        })

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities.handle_tool(
            "utility_get_cache_stats",
            {},
            mock_client
        )

        assert "Excellent" in result or "90.00%" in result

    @pytest.mark.asyncio
    async def test_cache_stats_performance_assessment_poor(self):
        """Test cache stats shows poor performance."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.get_stats = Mock(return_value={
            "enabled": True, "size": 10, "max_size": 1000,
            "hits": 30, "misses": 70, "hit_rate": "30.00%",
            "sets": 100, "evictions": 50, "expirations": 20, "total_requests": 100
        })

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities.handle_tool(
            "utility_get_cache_stats",
            {},
            mock_client
        )

        assert "30.00%" in result
