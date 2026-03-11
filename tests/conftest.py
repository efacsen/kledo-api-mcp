"""
Pytest configuration and shared fixtures for Kledo MCP Server tests
"""
import json
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, timedelta

from src.auth import KledoAuthenticator
from src.cache import KledoCache
from src.kledo_client import KledoAPIClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file from tests/fixtures/."""
    with open(FIXTURES_DIR / f"{name}.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv("KLEDO_EMAIL", "test@example.com")
    monkeypatch.setenv("KLEDO_PASSWORD", "test_password")
    monkeypatch.setenv("KLEDO_BASE_URL", "https://api.kledo.com/api/v1")
    monkeypatch.setenv("KLEDO_APP_CLIENT", "android")
    monkeypatch.setenv("CACHE_ENABLED", "true")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")


@pytest.fixture
def auth_credentials():
    """Provide test authentication credentials."""
    return {
        "email": "test@example.com",
        "password": "test_password",
        "base_url": "https://api.kledo.com/api/v1",
        "app_client": "android"
    }


@pytest.fixture
def mock_login_response():
    """Mock successful login response from Kledo API."""
    return {
        "data": {
            "data": {
                "access_token": "test_access_token_12345",
                "expires_in": 86400,
                "user": {
                    "id": 1,
                    "email": "test@example.com",
                    "name": "Test User"
                }
            }
        }
    }


@pytest.fixture
def mock_invoice_list_response():
    """Mock invoice list response loaded from real API fixture (3 statuses: unpaid/partial/paid)."""
    return load_fixture("invoices_list")


@pytest.fixture
def mock_invoice_detail_response():
    """Mock invoice detail response loaded from real API fixture."""
    # Wrap in data.data structure that tools expect
    detail_data = load_fixture("invoice_detail")
    return {"data": {"data": detail_data["data"]}}


@pytest.fixture
def mock_purchase_invoice_list_response():
    """Mock purchase invoice list response loaded from real API fixture."""
    return load_fixture("purchase_invoices_list")


@pytest.fixture
def mock_order_list_response():
    """Mock order list response loaded from real API fixture (statuses: open/partial/converted)."""
    return load_fixture("orders_list")


@pytest.fixture
def mock_order_detail_response():
    """Mock order detail response loaded from real API fixture."""
    return load_fixture("order_detail")


@pytest.fixture
def mock_delivery_list_response():
    """Mock delivery list response loaded from real API fixture."""
    return load_fixture("deliveries_list")


@pytest.fixture
def mock_delivery_detail_response():
    """Mock delivery detail response loaded from real API fixture."""
    return load_fixture("delivery_detail")


@pytest.fixture
def mock_contact_detail_response():
    """Mock contact detail response loaded from real API fixture."""
    return load_fixture("contact_detail")


@pytest.fixture
def mock_product_list_response():
    """Mock product list response loaded from real API fixture."""
    return load_fixture("products_list")


@pytest.fixture
def mock_contact_list_response():
    """Mock contact list response loaded from real API fixture."""
    return load_fixture("contacts_list")


@pytest.fixture
def mock_authenticator(auth_credentials):
    """Create a mock authenticator with pre-set token."""
    auth = KledoAuthenticator(**auth_credentials)
    auth._access_token = "test_access_token_12345"
    auth._token_expiry = datetime.now() + timedelta(hours=24)
    return auth


@pytest.fixture
def mock_cache():
    """Create a mock cache instance."""
    return KledoCache(enabled=True)


@pytest.fixture
async def mock_api_client(mock_authenticator, mock_cache):
    """Create a mock API client with authentication and cache."""
    client = KledoAPIClient(mock_authenticator, cache=mock_cache)
    return client


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx AsyncClient."""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value={"data": {"data": {}}})
    mock_response.raise_for_status = Mock()
    mock_client.request = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def sample_cache_config(tmp_path):
    """Create a temporary cache config file."""
    config_content = """
cache_tiers:
  master_data:
    products: 7200
    contacts: 7200
  transactional:
    invoices: 1800
    orders: 1800
  analytical:
    reports: 3600

cache_settings:
  max_size: 1000
  cleanup_interval: 300
"""
    config_file = tmp_path / "cache_config.yaml"
    config_file.write_text(config_content)
    return str(config_file)


@pytest.fixture
def sample_endpoints_config(tmp_path):
    """Create a temporary endpoints config file."""
    config_content = """
endpoints:
  invoices:
    list: /finance/invoices
    detail: /finance/invoices/{id}
    totals: /finance/invoices/totals
  products:
    list: /products
    detail: /products/{id}
  contacts:
    list: /contacts
    detail: /contacts/{id}
  reports:
    activity_team: /reports/activity-team
"""
    config_file = tmp_path / "endpoints.yaml"
    config_file.write_text(config_content)
    return str(config_file)
