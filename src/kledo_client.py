"""
Kledo API Client
"""
import httpx
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
from loguru import logger

from .auth import KledoAuthenticator
from .cache import KledoCache
from .utils.helpers import calculate_hash, clean_params


class KledoAPIClient:
    """Client for interacting with Kledo API."""

    def __init__(
        self,
        authenticator: KledoAuthenticator,
        cache: Optional[KledoCache] = None,
        endpoints_config: Optional[str] = None
    ):
        """
        Initialize Kledo API client.

        Args:
            authenticator: Authentication handler
            cache: Optional cache instance
            endpoints_config: Path to endpoints configuration file
        """
        self.auth = authenticator
        self.cache = cache
        self._endpoints: Dict[str, Any] = {}
        self._base_url = authenticator.base_url

        if endpoints_config:
            self._load_endpoints_config(endpoints_config)

        logger.info("Kledo API client initialized")

    def _load_endpoints_config(self, config_path: str) -> None:
        """Load endpoints configuration from YAML file."""
        try:
            path = Path(config_path)
            if not path.exists():
                logger.warning(f"Endpoints config file not found: {config_path}")
                return

            with open(path, 'r') as f:
                config = yaml.safe_load(f)

            self._endpoints = config.get("endpoints", {})
            logger.info(f"Loaded {len(self._endpoints)} endpoint categories")

        except Exception as e:
            logger.error(f"Error loading endpoints config: {str(e)}")

    def _get_endpoint(self, category: str, name: str) -> str:
        """
        Get endpoint URL from configuration.

        Args:
            category: Endpoint category (e.g., 'invoices', 'products')
            name: Endpoint name (e.g., 'list', 'detail')

        Returns:
            Endpoint path
        """
        endpoint = self._endpoints.get(category, {}).get(name)
        if not endpoint:
            raise ValueError(f"Endpoint not found: {category}.{name}")
        return endpoint

    def _build_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """
        Build cache key for request.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Cache key string
        """
        if params:
            param_hash = calculate_hash(params)
            return f"{endpoint}:{param_hash}"
        return endpoint

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        cache_category: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Kledo API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json: JSON body
            cache_category: Cache category for TTL lookup
            force_refresh: Skip cache and fetch fresh data

        Returns:
            Response data as dictionary

        Raises:
            httpx.HTTPStatusError: If request fails
        """
        # Ensure authenticated
        if not await self.auth.ensure_authenticated():
            raise ValueError("Failed to authenticate with Kledo API")

        # Build full URL
        url = f"{self._base_url}{endpoint}"

        # Check cache for GET requests
        if method.upper() == "GET" and self.cache and not force_refresh:
            cache_key = self._build_cache_key(endpoint, params)
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache hit for {endpoint}")
                return cached_data

        # Clean parameters
        if params:
            params = clean_params(params)

        # Make request
        try:
            headers = self.auth.get_auth_headers()
            headers["Content-Type"] = "application/json"

            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    headers=headers,
                    timeout=60.0
                )

                response.raise_for_status()
                data = response.json()

                # Cache successful GET responses
                if method.upper() == "GET" and self.cache:
                    cache_key = self._build_cache_key(endpoint, params)
                    self.cache.set(cache_key, data, category=cache_category or "default")
                    logger.debug(f"Cached response for {endpoint}")

                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code} error for {endpoint}")
            logger.debug(f"Response: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error for {endpoint}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {str(e)}")
            raise

    async def get(
        self,
        category: str,
        name: str,
        params: Optional[Dict[str, Any]] = None,
        path_params: Optional[Dict[str, Any]] = None,
        cache_category: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Make GET request using endpoint configuration.

        Args:
            category: Endpoint category
            name: Endpoint name
            params: Query parameters
            path_params: Path parameters (e.g., {id})
            cache_category: Cache category
            force_refresh: Skip cache

        Returns:
            Response data
        """
        endpoint = self._get_endpoint(category, name)

        # Replace path parameters
        if path_params:
            for key, value in path_params.items():
                endpoint = endpoint.replace(f"{{{key}}}", str(value))

        return await self._request(
            "GET",
            endpoint,
            params=params,
            cache_category=cache_category or category,
            force_refresh=force_refresh
        )

    async def get_raw(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        cache_category: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Make GET request to raw endpoint path.

        Args:
            endpoint: Full endpoint path
            params: Query parameters
            cache_category: Cache category
            force_refresh: Skip cache

        Returns:
            Response data
        """
        return await self._request(
            "GET",
            endpoint,
            params=params,
            cache_category=cache_category,
            force_refresh=force_refresh
        )

    # Convenience methods for common operations

    async def list_invoices(
        self,
        search: Optional[str] = None,
        contact_id: Optional[int] = None,
        status_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        due_date_from: Optional[str] = None,
        due_date_to: Optional[str] = None,
        per_page: int = 50,
        page: int = 1,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get list of sales invoices."""
        return await self.get(
            "invoices",
            "list",
            params={
                "search": search,
                "contact_id": contact_id,
                "status_id": status_id,
                "date_from": date_from,
                "date_to": date_to,
                "due_date_from": due_date_from,
                "due_date_to": due_date_to,
                "per_page": per_page,
                "page": page
            },
            cache_category="invoices",
            force_refresh=force_refresh
        )

    async def get_invoice_detail(self, invoice_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """Get invoice details."""
        return await self.get(
            "invoices",
            "detail",
            path_params={"id": invoice_id},
            cache_category="invoices",
            force_refresh=force_refresh
        )

    async def list_products(
        self,
        search: Optional[str] = None,
        per_page: int = 50,
        page: int = 1,
        include_warehouse_qty: bool = False,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get list of products."""
        return await self.get(
            "products",
            "list",
            params={
                "search": search,
                "per_page": per_page,
                "page": page,
                "include_warehouse_qty": 1 if include_warehouse_qty else 0
            },
            cache_category="products",
            force_refresh=force_refresh
        )

    async def list_contacts(
        self,
        search: Optional[str] = None,
        type_id: Optional[int] = None,
        per_page: int = 50,
        page: int = 1,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get list of contacts."""
        return await self.get(
            "contacts",
            "list",
            params={
                "search": search,
                "type_id": type_id,
                "per_page": per_page,
                "page": page
            },
            cache_category="contacts",
            force_refresh=force_refresh
        )

    async def get_activity_team_report(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get team activity report."""
        return await self.get(
            "reports",
            "activity_team",
            params={
                "date_from": date_from,
                "date_to": date_to
            },
            cache_category="reports",
            force_refresh=force_refresh
        )
