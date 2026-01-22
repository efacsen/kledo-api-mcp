"""
Authentication handler for Kledo API
"""
import httpx
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger


class KledoAuthenticator:
    """Handles authentication with Kledo API."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        app_client: str = "android"
    ):
        """
        Initialize authenticator.

        Supports two authentication methods:
        1. API Key (recommended) - Static token, no login required
        2. Email/Password (legacy) - Dynamic token via login endpoint

        Args:
            base_url: API base URL
            api_key: Kledo API key (e.g., kledo_pat_xxx) - recommended
            email: Kledo account email (fallback method)
            password: Kledo account password (fallback method)
            app_client: Device type (android/ios) - only for email/password auth

        Raises:
            ValueError: If neither api_key nor (email and password) is provided
        """
        self.base_url = base_url.rstrip("/")
        self.app_client = app_client

        # Determine authentication method
        if api_key:
            self.auth_method = "api_key"
            self.api_key = api_key
            self._access_token = None
            self._token_expiry = None
            logger.info("Using API key authentication (recommended)")
        elif email and password:
            self.auth_method = "email_password"
            self.email = email
            self.password = password
            self.api_key = None
            self._access_token: Optional[str] = None
            self._token_expiry: Optional[datetime] = None
            logger.info("Using email/password authentication (legacy)")
        else:
            raise ValueError(
                "Must provide either api_key or (email and password). "
                "API key authentication is recommended for security."
            )

    @property
    def access_token(self) -> Optional[str]:
        """Get current access token."""
        return self._access_token

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated with valid token."""
        # API key is always valid (doesn't expire)
        if self.auth_method == "api_key":
            return True

        # Email/password requires valid token
        if not self._access_token:
            return False

        if self._token_expiry and datetime.now() >= self._token_expiry:
            logger.warning("Access token has expired")
            return False

        return True

    async def login(self) -> bool:
        """
        Perform login to Kledo API.

        For API key authentication: Always returns True (no login needed).
        For email/password: Performs actual login request.

        Returns:
            True if login successful, False otherwise
        """
        # API key doesn't need login
        if self.auth_method == "api_key":
            logger.debug("API key auth - no login required")
            return True

        # Email/password login flow
        logger.info(f"Attempting to login to Kledo API as {self.email}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/authentication/singleLogin",
                    headers={
                        "app-client": self.app_client,
                        "Content-Type": "application/json"
                    },
                    json={
                        "email": self.email,
                        "password": self.password
                    },
                    timeout=30.0
                )

                response.raise_for_status()
                data = response.json()

                # Extract access token from response
                # Expected path: data.data.access_token
                if data.get("data", {}).get("data", {}).get("access_token"):
                    self._access_token = data["data"]["data"]["access_token"]

                    # Set token expiry (default to 24 hours if not specified)
                    expires_in = data["data"]["data"].get("expires_in", 86400)
                    self._token_expiry = datetime.now() + timedelta(seconds=expires_in)

                    logger.info("Successfully authenticated with Kledo API")
                    logger.debug(f"Token will expire at: {self._token_expiry}")
                    return True
                else:
                    logger.error("Access token not found in response")
                    logger.debug(f"Response data: {data}")
                    return False

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during login: {e.response.status_code}")
            logger.debug(f"Response: {e.response.text}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Network error during login: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            return False

    async def logout(self) -> bool:
        """
        Logout from Kledo API.

        For API key authentication: No-op (API keys don't have sessions).
        For email/password: Performs actual logout request.

        Returns:
            True if logout successful
        """
        # API key doesn't have sessions to logout
        if self.auth_method == "api_key":
            logger.debug("API key auth - no logout required")
            return True

        # Email/password logout flow
        if not self.is_authenticated:
            logger.warning("Cannot logout: not authenticated")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/authentication/logout",
                    headers={
                        "Authorization": f"Bearer {self._access_token}",
                        "app-client": self.app_client
                    },
                    timeout=30.0
                )

                response.raise_for_status()
                logger.info("Successfully logged out from Kledo API")

        except Exception as e:
            logger.warning(f"Error during logout: {str(e)}")
        finally:
            # Clear token regardless of logout success
            self._access_token = None
            self._token_expiry = None

        return True

    async def ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid authentication token.
        Re-authenticate if necessary.

        Returns:
            True if authenticated, False otherwise
        """
        if self.is_authenticated:
            return True

        logger.info("Token expired or missing, re-authenticating...")
        return await self.login()

    def get_auth_headers(self) -> dict:
        """
        Get authentication headers for API requests.

        Returns:
            Dictionary of headers with Authorization bearer token
        """
        if not self.is_authenticated:
            raise ValueError("Not authenticated. Call login() first.")

        # API key uses the key directly as bearer token
        if self.auth_method == "api_key":
            return {
                "Authorization": f"Bearer {self.api_key}"
            }

        # Email/password uses session token
        return {
            "Authorization": f"Bearer {self._access_token}",
            "app-client": self.app_client
        }
