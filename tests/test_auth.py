"""
Tests for Kledo authentication module
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, Mock
import httpx

from src.auth import KledoAuthenticator


class TestKledoAuthenticator:
    """Test suite for KledoAuthenticator class."""

    def test_init(self, auth_credentials):
        """Test authenticator initialization."""
        auth = KledoAuthenticator(**auth_credentials)

        assert auth.email == auth_credentials["email"]
        assert auth.password == auth_credentials["password"]
        assert auth.base_url == auth_credentials["base_url"]
        assert auth.app_client == auth_credentials["app_client"]
        assert auth.access_token is None
        assert not auth.is_authenticated

    def test_base_url_stripping(self):
        """Test that base URL trailing slash is stripped."""
        auth = KledoAuthenticator(
            email="test@example.com",
            password="password",
            base_url="https://api.kledo.com/api/v1/",
            app_client="android"
        )
        assert auth.base_url == "https://api.kledo.com/api/v1"

    def test_is_authenticated_no_token(self, auth_credentials):
        """Test is_authenticated returns False when no token."""
        auth = KledoAuthenticator(**auth_credentials)
        assert not auth.is_authenticated

    def test_is_authenticated_with_valid_token(self, auth_credentials):
        """Test is_authenticated returns True with valid token."""
        auth = KledoAuthenticator(**auth_credentials)
        auth._access_token = "test_token"
        auth._token_expiry = datetime.now() + timedelta(hours=1)

        assert auth.is_authenticated

    def test_is_authenticated_with_expired_token(self, auth_credentials):
        """Test is_authenticated returns False with expired token."""
        auth = KledoAuthenticator(**auth_credentials)
        auth._access_token = "test_token"
        auth._token_expiry = datetime.now() - timedelta(hours=1)

        assert not auth.is_authenticated

    @pytest.mark.asyncio
    async def test_login_success(self, auth_credentials, mock_login_response):
        """Test successful login."""
        auth = KledoAuthenticator(**auth_credentials)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value=mock_login_response)
            mock_response.raise_for_status = Mock()

            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await auth.login()

            assert result is True
            assert auth.access_token == "test_access_token_12345"
            assert auth.is_authenticated
            assert auth._token_expiry is not None

    @pytest.mark.asyncio
    async def test_login_failure_no_token_in_response(self, auth_credentials):
        """Test login failure when token not in response."""
        auth = KledoAuthenticator(**auth_credentials)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {}}
            mock_response.raise_for_status = Mock()

            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await auth.login()

            assert result is False
            assert auth.access_token is None
            assert not auth.is_authenticated

    @pytest.mark.asyncio
    async def test_login_http_error(self, auth_credentials):
        """Test login with HTTP error."""
        auth = KledoAuthenticator(**auth_credentials)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized", request=Mock(), response=mock_response
            )

            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await auth.login()

            assert result is False
            assert not auth.is_authenticated

    @pytest.mark.asyncio
    async def test_login_network_error(self, auth_credentials):
        """Test login with network error."""
        auth = KledoAuthenticator(**auth_credentials)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.RequestError("Network error")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await auth.login()

            assert result is False

    @pytest.mark.asyncio
    async def test_logout_success(self, mock_authenticator):
        """Test successful logout."""
        auth = mock_authenticator
        assert auth.is_authenticated

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()

            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await auth.logout()

            assert result is True
            assert auth.access_token is None
            assert not auth.is_authenticated

    @pytest.mark.asyncio
    async def test_logout_not_authenticated(self, auth_credentials):
        """Test logout when not authenticated."""
        auth = KledoAuthenticator(**auth_credentials)

        result = await auth.logout()

        assert result is False

    @pytest.mark.asyncio
    async def test_logout_clears_token_on_error(self, mock_authenticator):
        """Test logout clears token even on error."""
        auth = mock_authenticator

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Network error")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await auth.logout()

            assert result is True
            assert auth.access_token is None

    @pytest.mark.asyncio
    async def test_ensure_authenticated_already_authenticated(self, mock_authenticator):
        """Test ensure_authenticated when already authenticated."""
        auth = mock_authenticator

        result = await auth.ensure_authenticated()

        assert result is True

    @pytest.mark.asyncio
    async def test_ensure_authenticated_needs_login(self, auth_credentials, mock_login_response):
        """Test ensure_authenticated performs login when needed."""
        auth = KledoAuthenticator(**auth_credentials)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value=mock_login_response)
            mock_response.raise_for_status = Mock()

            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await auth.ensure_authenticated()

            assert result is True
            assert auth.is_authenticated

    def test_get_auth_headers_authenticated(self, mock_authenticator):
        """Test getting auth headers when authenticated."""
        auth = mock_authenticator

        headers = auth.get_auth_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_access_token_12345"
        assert headers["app-client"] == "android"

    def test_get_auth_headers_not_authenticated(self, auth_credentials):
        """Test getting auth headers when not authenticated raises error."""
        auth = KledoAuthenticator(**auth_credentials)

        with pytest.raises(ValueError, match="Not authenticated"):
            auth.get_auth_headers()
