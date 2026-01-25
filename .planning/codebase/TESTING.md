# Testing Patterns

**Analysis Date:** 2026-01-21

## Test Framework

**Runner:**
- pytest 7.4.0+
- Config: `pytest.ini` or `pyproject.toml` (project uses standard pytest discovery)
- pytest-asyncio 0.21.0+ for async test support (marked with `@pytest.mark.asyncio`)
- pytest-cov 4.1.0+ for coverage reporting

**Assertion Library:**
- Standard pytest assertions: `assert`, `assert result is True`, `assert not auth.is_authenticated`
- pytest.raises for exception testing: `with pytest.raises(ValueError, match="pattern"):`

**Run Commands:**
```bash
pytest                          # Run all tests
pytest -v                       # Run all tests with verbose output
pytest --asyncio-mode=auto      # Run with async support auto-enabled
pytest --cov=src                # Run with coverage for src/
pytest -k test_login            # Run tests matching pattern
pytest tests/test_auth.py       # Run specific test file
```

## Test File Organization

**Location:**
- Co-located separate pattern: `tests/` directory mirrors `src/` structure
- Test files correspond to source modules: `src/auth.py` → `tests/test_auth.py`, `src/kledo_client.py` → `tests/test_kledo_client.py`
- Directory: `/Users/kevinzakaria/developers/kledo-api-mcp/tests/`

**Naming:**
- Test files prefixed with `test_`: `test_auth.py`, `test_kledo_client.py`, `test_cache.py`
- Test classes use `Test` prefix: `TestKledoAuthenticator`, `TestKledoAPIClient`
- Test methods use `test_` prefix with descriptive suffix: `test_init`, `test_login_success`, `test_login_http_error`

**Structure:**
```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_auth.py                   # Tests for src/auth.py
├── test_kledo_client.py           # Tests for src/kledo_client.py
├── test_cache.py                  # Tests for src/cache.py
├── test_server.py                 # Tests for src/server.py
├── test_tools_invoices.py         # Tests for src/tools/invoices.py
├── test_tools_products.py         # Tests for src/tools/products.py
├── test_tools_orders.py           # Tests for src/tools/orders.py
├── test_tools_contacts.py         # Tests for src/tools/contacts.py
├── test_tools_deliveries.py       # Tests for src/tools/deliveries.py
├── test_tools_financial.py        # Tests for src/tools/financial.py
└── test_tools_utilities.py        # Tests for src/tools/utilities.py
```

## Test Structure

**Suite Organization:**
Tests use class-based organization grouping related tests:
```python
class TestKledoAuthenticator:
    """Test suite for KledoAuthenticator class."""

    def test_init(self, auth_credentials):
        """Test authenticator initialization."""
        # Arrange
        # Act
        # Assert

    @pytest.mark.asyncio
    async def test_login_success(self, auth_credentials, mock_login_response):
        """Test successful login."""
        # Arrange
        # Act
        # Assert
```

**Patterns:**
- **Setup pattern:** Test classes with method-level fixtures; setup via fixtures passed as parameters
- **Teardown pattern:** Fixtures handle cleanup through context managers and lifecycle; no explicit teardown methods observed
- **Assertion pattern:** Direct assertions with clear naming: `assert result is True`, `assert auth.access_token == "expected_value"`

Example from `tests/test_auth.py`:
```python
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
```

## Mocking

**Framework:** unittest.mock (standard library)
- `AsyncMock` for async functions
- `Mock` for synchronous functions
- `patch` context manager for patching external dependencies
- `MagicMock` for complex mocking scenarios

**Patterns:**
HTTP client mocking pattern for httpx (from `tests/test_auth.py`):
```python
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
```

Async context manager mocking:
```python
mock_client.__aenter__ = AsyncMock(return_value=mock_client)
mock_client.__aexit__ = AsyncMock(return_value=None)
```

Side effect for exceptions:
```python
mock_client.post.side_effect = httpx.RequestError("Network error")
```

**What to Mock:**
- External HTTP calls (httpx.AsyncClient requests)
- Environment variables (via pytest's `monkeypatch` fixture)
- File I/O (YAML config loading)
- Authentication tokens and responses
- API responses and data structures

**What NOT to Mock:**
- Core business logic: actual authentication flow checking, token expiry logic
- Cache behavior: use real cache instances to test cache hit/miss logic
- Helper functions: use real helpers to test data transformation
- Type checking and validation

## Fixtures and Factories

**Test Data:**
Fixtures defined in `conftest.py` (located at `/Users/kevinzakaria/developers/kledo-api-mcp/tests/conftest.py`):

Authentication fixtures:
```python
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
                "user": {"id": 1, "email": "test@example.com", "name": "Test User"}
            }
        }
    }
```

API response fixtures:
```python
@pytest.fixture
def mock_invoice_list_response():
    """Mock invoice list response."""
    return {
        "data": {
            "data": [
                {
                    "id": 1,
                    "trans_number": "INV-001",
                    "contact_name": "Customer A",
                    "trans_date": "2024-01-15",
                    "due_date": "2024-02-15",
                    "grand_total": 1000.0,
                    "amount_paid": 500.0,
                    "status_name": "Partially Paid"
                }
            ],
            "pagination": {"current_page": 1, "total_pages": 1, "total": 2}
        }
    }
```

Instance fixtures:
```python
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
```

Configuration fixtures:
```python
@pytest.fixture
def sample_endpoints_config(tmp_path):
    """Create a temporary endpoints config file."""
    config_content = """
endpoints:
  invoices:
    list: /finance/invoices
    detail: /finance/invoices/{id}
"""
    config_file = tmp_path / "endpoints.yaml"
    config_file.write_text(config_content)
    return str(config_file)
```

**Location:**
- All fixtures in `tests/conftest.py`
- Session-scoped fixtures for expensive setup: `@pytest.fixture(scope="session")`
- Function-scoped fixtures (default) for test isolation
- Data fixtures return dictionaries or objects for reuse

## Coverage

**Requirements:** Not explicitly enforced; project includes pytest-cov in `requirements.txt`

**View Coverage:**
```bash
pytest --cov=src --cov-report=html     # Generate HTML coverage report
pytest --cov=src --cov-report=term     # Terminal coverage report
pytest --cov=src --cov-report=xml      # XML coverage report
```

## Test Types

**Unit Tests:**
- Scope: Individual classes and functions
- Approach: Isolated tests with mocked dependencies
- Examples:
  - `test_init()`: Constructor initialization
  - `test_base_url_stripping()`: String processing
  - `test_is_authenticated_*()`: Property behavior
  - `test_get_endpoint_*()`: Method behavior with various inputs

**Integration Tests:**
- Scope: Interaction between components (auth + cache + client)
- Approach: Real instances or fixtures representing real behavior
- Examples:
  - Async tests combining authentication and API calls
  - Client tests with real cache behavior
  - Configuration loading tests

**E2E Tests:**
- Framework: Not implemented; would require live API access
- Note: Project is MCP server for external API; full E2E would require Kledo API credentials

## Common Patterns

**Async Testing:**
All async tests marked with `@pytest.mark.asyncio` decorator:
```python
@pytest.mark.asyncio
async def test_login_success(self, auth_credentials, mock_login_response):
    """Test successful login."""
    auth = KledoAuthenticator(**auth_credentials)
    # Test async code...
    result = await auth.login()
    assert result is True
```

Event loop fixture for session scope:
```python
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

**Error Testing:**
Exception assertions with pytest.raises:
```python
def test_get_auth_headers_not_authenticated(self, auth_credentials):
    """Test getting auth headers when not authenticated raises error."""
    auth = KledoAuthenticator(**auth_credentials)

    with pytest.raises(ValueError, match="Not authenticated"):
        auth.get_auth_headers()
```

HTTP error testing:
```python
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
```

---

*Testing analysis: 2026-01-21*
