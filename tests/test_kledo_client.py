"""
Tests for Kledo API Client
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from src.kledo_client import KledoAPIClient
from src.auth import KledoAuthenticator
from src.cache import KledoCache


class TestKledoAPIClient:
    """Test suite for KledoAPIClient class."""

    def test_init_basic(self, mock_authenticator):
        """Test basic client initialization."""
        client = KledoAPIClient(mock_authenticator)

        assert client.auth == mock_authenticator
        assert client.cache is None
        assert client._base_url == mock_authenticator.base_url

    def test_init_with_cache(self, mock_authenticator, mock_cache):
        """Test client initialization with cache."""
        client = KledoAPIClient(mock_authenticator, cache=mock_cache)

        assert client.cache == mock_cache

    def test_init_with_endpoints_config(self, mock_authenticator, sample_endpoints_config):
        """Test client initialization with endpoints config."""
        client = KledoAPIClient(
            mock_authenticator,
            endpoints_config=sample_endpoints_config
        )

        assert len(client._endpoints) > 0
        assert "invoices" in client._endpoints

    def test_get_endpoint_success(self, mock_authenticator, sample_endpoints_config):
        """Test getting endpoint from config."""
        client = KledoAPIClient(
            mock_authenticator,
            endpoints_config=sample_endpoints_config
        )

        endpoint = client._get_endpoint("invoices", "list")

        assert endpoint == "/finance/invoices"

    def test_get_endpoint_not_found(self, mock_authenticator, sample_endpoints_config):
        """Test getting non-existent endpoint raises error."""
        client = KledoAPIClient(
            mock_authenticator,
            endpoints_config=sample_endpoints_config
        )

        with pytest.raises(ValueError, match="Endpoint not found"):
            client._get_endpoint("nonexistent", "list")

    def test_build_cache_key_no_params(self, mock_authenticator):
        """Test building cache key without params."""
        client = KledoAPIClient(mock_authenticator)

        key = client._build_cache_key("/test/endpoint")

        assert key == "/test/endpoint"

    def test_build_cache_key_with_params(self, mock_authenticator):
        """Test building cache key with params."""
        client = KledoAPIClient(mock_authenticator)

        params = {"search": "test", "page": 1}
        key = client._build_cache_key("/test/endpoint", params)

        assert key.startswith("/test/endpoint:")
        assert len(key) > len("/test/endpoint:")

    @pytest.mark.asyncio
    async def test_request_get_success(self, mock_authenticator):
        """Test successful GET request."""
        client = KledoAPIClient(mock_authenticator)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={"data": {"result": "success"}})
            mock_response.raise_for_status = Mock()

            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await client._request("GET", "/test/endpoint")

            assert result == {"data": {"result": "success"}}

    @pytest.mark.asyncio
    async def test_request_with_cache_hit(self, mock_authenticator, mock_cache):
        """Test GET request with cache hit."""
        client = KledoAPIClient(mock_authenticator, cache=mock_cache)

        # Pre-populate cache
        cache_key = client._build_cache_key("/test/endpoint", None)
        mock_cache.set(cache_key, {"cached": "data"}, category="default")

        result = await client._request("GET", "/test/endpoint")

        assert result == {"cached": "data"}
        assert mock_cache._stats["hits"] == 1

    @pytest.mark.asyncio
    async def test_request_cache_miss_and_set(self, mock_authenticator, mock_cache):
        """Test GET request with cache miss and subsequent caching."""
        client = KledoAPIClient(mock_authenticator, cache=mock_cache)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={"data": "fresh"})
            mock_response.raise_for_status = Mock()

            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await client._request("GET", "/test/endpoint", cache_category="default")

            assert result == {"data": "fresh"}
            assert mock_cache._stats["sets"] == 1

    @pytest.mark.asyncio
    async def test_request_force_refresh(self, mock_authenticator, mock_cache):
        """Test request with force_refresh skips cache."""
        client = KledoAPIClient(mock_authenticator, cache=mock_cache)

        # Pre-populate cache
        cache_key = client._build_cache_key("/test/endpoint", None)
        mock_cache.set(cache_key, {"cached": "old"}, category="default")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={"data": "fresh"})
            mock_response.raise_for_status = Mock()

            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await client._request(
                "GET",
                "/test/endpoint",
                force_refresh=True
            )

            assert result == {"data": "fresh"}

    @pytest.mark.asyncio
    async def test_request_http_error(self, mock_authenticator):
        """Test request handling HTTP error."""
        client = KledoAPIClient(mock_authenticator)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not found"
            mock_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
                "Not found", request=Mock(), response=mock_response
            ))

            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await client._request("GET", "/test/endpoint")

    @pytest.mark.asyncio
    async def test_request_network_error(self, mock_authenticator):
        """Test request handling network error."""
        client = KledoAPIClient(mock_authenticator)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.side_effect = httpx.RequestError("Network error")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.RequestError):
                await client._request("GET", "/test/endpoint")

    @pytest.mark.asyncio
    async def test_request_not_authenticated(self, auth_credentials):
        """Test request fails when not authenticated."""
        auth = KledoAuthenticator(**auth_credentials)
        client = KledoAPIClient(auth)

        with pytest.raises(ValueError, match="Failed to authenticate"):
            await client._request("GET", "/test/endpoint")

    @pytest.mark.asyncio
    async def test_get_with_path_params(self, mock_authenticator, sample_endpoints_config):
        """Test GET request with path parameters."""
        client = KledoAPIClient(
            mock_authenticator,
            endpoints_config=sample_endpoints_config
        )

        with patch.object(client, "_request", new=AsyncMock(return_value={"data": "success"})):
            result = await client.get(
                "invoices",
                "detail",
                path_params={"id": 123}
            )

            assert result == {"data": "success"}
            # Verify the path param was replaced
            client._request.assert_called_once()
            call_args = client._request.call_args
            assert "/finance/invoices/123" in str(call_args)

    @pytest.mark.asyncio
    async def test_get_raw(self, mock_authenticator):
        """Test raw GET request."""
        client = KledoAPIClient(mock_authenticator)

        with patch.object(client, "_request", new=AsyncMock(return_value={"data": "success"})):
            result = await client.get_raw(
                "/custom/endpoint",
                params={"test": "value"}
            )

            assert result == {"data": "success"}
            client._request.assert_called_once_with(
                "GET",
                "/custom/endpoint",
                params={"test": "value"},
                cache_category=None,
                force_refresh=False
            )

    @pytest.mark.asyncio
    async def test_list_invoices(self, mock_authenticator, mock_invoice_list_response):
        """Test list_invoices convenience method."""
        client = KledoAPIClient(mock_authenticator)

        with patch.object(
            client,
            "get",
            new=AsyncMock(return_value=mock_invoice_list_response)
        ):
            result = await client.list_invoices(
                search="test",
                contact_id=1,
                per_page=10
            )

            assert result == mock_invoice_list_response
            client.get.assert_called_once()
            call_kwargs = client.get.call_args.kwargs
            assert call_kwargs["params"]["search"] == "test"
            assert call_kwargs["params"]["contact_id"] == 1
            assert call_kwargs["params"]["per_page"] == 10

    @pytest.mark.asyncio
    async def test_get_invoice_detail(self, mock_authenticator, mock_invoice_detail_response):
        """Test get_invoice_detail convenience method."""
        client = KledoAPIClient(mock_authenticator)

        with patch.object(
            client,
            "get",
            new=AsyncMock(return_value=mock_invoice_detail_response)
        ):
            result = await client.get_invoice_detail(123)

            assert result == mock_invoice_detail_response
            client.get.assert_called_once()
            call_kwargs = client.get.call_args.kwargs
            assert call_kwargs["path_params"]["id"] == 123

    @pytest.mark.asyncio
    async def test_list_products(self, mock_authenticator, mock_product_list_response):
        """Test list_products convenience method."""
        client = KledoAPIClient(mock_authenticator)

        with patch.object(
            client,
            "get",
            new=AsyncMock(return_value=mock_product_list_response)
        ):
            result = await client.list_products(
                search="test",
                include_warehouse_qty=True
            )

            assert result == mock_product_list_response
            client.get.assert_called_once()
            call_kwargs = client.get.call_args.kwargs
            assert call_kwargs["params"]["include_warehouse_qty"] == 1

    @pytest.mark.asyncio
    async def test_list_contacts(self, mock_authenticator, mock_contact_list_response):
        """Test list_contacts convenience method."""
        client = KledoAPIClient(mock_authenticator)

        with patch.object(
            client,
            "get",
            new=AsyncMock(return_value=mock_contact_list_response)
        ):
            result = await client.list_contacts(type_id=1)

            assert result == mock_contact_list_response

    @pytest.mark.asyncio
    async def test_get_activity_team_report(self, mock_authenticator):
        """Test get_activity_team_report convenience method."""
        client = KledoAPIClient(mock_authenticator)

        expected_response = {"data": {"data": {"team_activity": []}}}

        with patch.object(
            client,
            "get",
            new=AsyncMock(return_value=expected_response)
        ):
            result = await client.get_activity_team_report(
                date_from="2024-01-01",
                date_to="2024-01-31"
            )

            assert result == expected_response
            client.get.assert_called_once()
            call_kwargs = client.get.call_args.kwargs
            assert call_kwargs["params"]["date_from"] == "2024-01-01"
            assert call_kwargs["params"]["date_to"] == "2024-01-31"
