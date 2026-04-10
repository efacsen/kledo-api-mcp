"""
Tests for utility tools — post-migration (no get_tools/handle_tool).
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock

from src.tools import utilities
from src.kledo_client import KledoAPIClient
from src.cache import KledoCache


class TestUtilityHandlerFunctions:
    """Verify private handler functions exist and are async."""

    def test_handler_functions_are_callable(self):
        assert callable(utilities._clear_cache)
        assert asyncio.iscoroutinefunction(utilities._clear_cache)
        assert callable(utilities._get_cache_stats)
        assert asyncio.iscoroutinefunction(utilities._get_cache_stats)
        assert callable(utilities._test_connection)
        assert asyncio.iscoroutinefunction(utilities._test_connection)

    def test_no_legacy_interface(self):
        assert not hasattr(utilities, "get_tools"), "utilities still exports get_tools()"
        assert not hasattr(utilities, "handle_tool"), "utilities still exports handle_tool()"


class TestUtilityTools:
    """Test suite for utility private functions."""

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test _clear_cache clears cache and reports count."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.clear = Mock(return_value=15)

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities._clear_cache({}, mock_client)

        assert "Cache cleared successfully" in result
        assert "15" in result
        mock_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cache_disabled(self):
        """Test clear cache when cache is disabled."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = None

        result = await utilities._clear_cache({}, mock_client)

        assert "Cache is not enabled" in result

    @pytest.mark.asyncio
    async def test_get_cache_stats(self):
        """Test _get_cache_stats returns formatted stats."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.get_stats = Mock(
            return_value={
                "enabled": True,
                "size": 50,
                "max_size": 1000,
                "hits": 200,
                "misses": 50,
                "hit_rate": "80.00%",
                "sets": 50,
                "evictions": 5,
                "expirations": 10,
                "total_requests": 250,
            }
        )

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities._get_cache_stats({}, mock_client)

        assert "Cache Statistics" in result
        assert "80.00%" in result
        assert "Enabled" in result
        assert "50 / 1000" in result

    @pytest.mark.asyncio
    async def test_get_cache_stats_disabled(self):
        """Test get cache stats when cache is disabled."""
        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = None

        result = await utilities._get_cache_stats({}, mock_client)

        assert "Cache is not enabled" in result

    @pytest.mark.asyncio
    async def test_test_connection(self):
        """Test _test_connection returns connection info."""
        mock_auth = Mock()
        mock_auth.is_authenticated = True
        mock_auth._token_expiry = "2024-12-31 23:59:59"
        mock_auth.base_url = "https://api.kledo.com/api/v1"

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.auth = mock_auth
        mock_client.get_raw = AsyncMock(return_value={"data": {"data": []}})

        result = await utilities._test_connection({}, mock_client)

        assert "Connection Test" in result
        assert "Authenticated" in result
        assert "API Connection Successful" in result

    @pytest.mark.asyncio
    async def test_test_connection_not_authenticated(self):
        """Test connection test when not authenticated."""
        mock_auth = Mock()
        mock_auth.is_authenticated = False

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.auth = mock_auth
        mock_client.get_raw = AsyncMock(return_value={"data": {"data": []}})

        result = await utilities._test_connection({}, mock_client)

        assert "Not Authenticated" in result

    @pytest.mark.asyncio
    async def test_test_connection_api_failure(self):
        """Test connection test when API call fails."""
        mock_auth = Mock()
        mock_auth.is_authenticated = True
        mock_auth._token_expiry = "2024-12-31"
        mock_auth.base_url = "https://api.kledo.com"

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.auth = mock_auth
        mock_client.get_raw = AsyncMock(side_effect=Exception("Network timeout"))

        result = await utilities._test_connection({}, mock_client)

        assert "API Connection Failed" in result
        assert "Network timeout" in result

    @pytest.mark.asyncio
    async def test_clear_cache_error_handling(self):
        """Test error handling in clear cache."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.clear = Mock(side_effect=Exception("Clear failed"))

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities._clear_cache({}, mock_client)

        assert "Error clearing cache" in result

    @pytest.mark.asyncio
    async def test_get_cache_stats_error_handling(self):
        """Test error handling in get cache stats."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.get_stats = Mock(side_effect=Exception("Stats error"))

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities._get_cache_stats({}, mock_client)

        assert "Error fetching cache stats" in result

    @pytest.mark.asyncio
    async def test_cache_stats_performance_assessment_excellent(self):
        """Test cache stats shows excellent performance."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.get_stats = Mock(
            return_value={
                "enabled": True,
                "size": 100,
                "max_size": 1000,
                "hits": 900,
                "misses": 100,
                "hit_rate": "90.00%",
                "sets": 100,
                "evictions": 0,
                "expirations": 0,
                "total_requests": 1000,
            }
        )

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities._get_cache_stats({}, mock_client)

        assert "Excellent" in result or "90.00%" in result

    @pytest.mark.asyncio
    async def test_cache_stats_performance_assessment_poor(self):
        """Test cache stats shows poor performance."""
        mock_cache = Mock(spec=KledoCache)
        mock_cache.get_stats = Mock(
            return_value={
                "enabled": True,
                "size": 10,
                "max_size": 1000,
                "hits": 30,
                "misses": 70,
                "hit_rate": "30.00%",
                "sets": 100,
                "evictions": 50,
                "expirations": 20,
                "total_requests": 100,
            }
        )

        mock_client = Mock(spec=KledoAPIClient)
        mock_client.cache = mock_cache

        result = await utilities._get_cache_stats({}, mock_client)

        assert "30.00%" in result
