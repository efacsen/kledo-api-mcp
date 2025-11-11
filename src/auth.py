"""
Authentication handler for Kledo API
"""
import httpx
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger


class KledoAuthenticator:
    """Handles authentication with Kledo API."""

    def __init__(self, email: str, password: str, base_url: str, app_client: str = "android"):
        """
        Initialize authenticator.

        Args:
            email: Kledo account email
            password: Kledo account password
            base_url: API base URL
            app_client: Device type (android/ios)
        """
        self.email = email
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.app_client = app_client

        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    @property
    def access_token(self) -> Optional[str]:
        """Get current access token."""
        return self._access_token

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated with valid token."""
        if not self._access_token:
            return False

        if self._token_expiry and datetime.now() >= self._token_expiry:
            logger.warning("Access token has expired")
            return False

        return True

    async def login(self) -> bool:
        """
        Perform login to Kledo API.

        Returns:
            True if login successful, False otherwise
        """
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

        Returns:
            True if logout successful
        """
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
            Dictionary of headers
        """
        if not self.is_authenticated:
            raise ValueError("Not authenticated. Call login() first.")

        return {
            "Authorization": f"Bearer {self._access_token}",
            "app-client": self.app_client
        }
