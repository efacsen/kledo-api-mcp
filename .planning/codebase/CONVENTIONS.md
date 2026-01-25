# Coding Conventions

**Analysis Date:** 2026-01-21

## Naming Patterns

**Files:**
- Lowercase with underscores for modules: `kledo_client.py`, `auth.py`, `helpers.py`
- Descriptive module names indicating purpose: `cache.py`, `server.py`
- Tool modules grouped by domain: `invoices.py`, `products.py`, `orders.py`, `contacts.py`, etc. in `src/tools/`
- Test files match source modules with `test_` prefix: `test_auth.py`, `test_kledo_client.py`

**Functions:**
- Use `snake_case` for all functions: `handle_tool()`, `list_products()`, `parse_date_range()`
- Public async functions use descriptive verbs: `login()`, `logout()`, `ensure_authenticated()`
- Private functions prefixed with underscore: `_request()`, `_get_endpoint()`, `_load_endpoints_config()`
- Tool handler functions follow pattern `async def handle_tool()` as entry point
- Tool operation functions prefixed with underscore: `_list_products()`, `_get_product_detail()`
- Getter/setter properties use descriptive names: `access_token`, `is_authenticated`, `is_expired`

**Variables:**
- `snake_case` for all local and instance variables: `access_token`, `base_url`, `cache_key`, `mock_response`
- Private instance variables prefixed with underscore: `_access_token`, `_token_expiry`, `_endpoints`, `_base_url`
- Constants implicit through context (no ALL_CAPS convention enforced)
- Explicit temporary variables for clarity: `cache_key`, `auth_headers`, `response_data`

**Types:**
- Classes use `PascalCase`: `KledoAuthenticator`, `KledoAPIClient`, `KledoCache`, `CacheEntry`
- Type hints consistently used with modern Python syntax: `Optional[str]`, `Dict[str, Any]`, `list[Tool]`
- Union syntax with `|` for optional types: `KledoAPIClient | None` (modern Python 3.10+)

## Code Style

**Formatting:**
- Black for code formatting (listed in `requirements.txt`)
- Line length implied standard (observed code uses reasonable line lengths under 100 chars for most statements)
- String formatting with f-strings throughout: `f"Error: {str(e)}"`, `f"{self._base_url}{endpoint}"`
- Docstring style: triple-quoted on same line for short docstrings, multi-line for longer docs

**Linting:**
- Ruff linter included in `requirements.txt` for code quality
- Mypy type checker included for static type analysis
- Code follows consistent import organization and structure

## Import Organization

**Order:**
1. Standard library imports: `os`, `asyncio`, `sys`, `time`, `hashlib`, `json`
2. Third-party imports: `httpx`, `yaml`, `pydantic`, `loguru`, `mcp`
3. Local imports: Relative imports with dot notation: `from ..kledo_client import`, `from ..utils.helpers import`

**Path Aliases:**
- No path aliases configured; uses relative imports for clarity
- Relative imports from package root: `from src.auth import`, `from src.cache import` (in tests)
- Relative imports within modules: `from ..kledo_client import` (from `src/tools/`)

## Error Handling

**Patterns:**
- Explicit exception handling with specific exception types:
  - `httpx.HTTPStatusError` for HTTP failures
  - `httpx.RequestError` for network errors
  - Generic `Exception` as fallback for unexpected errors
- Try-catch blocks log errors with `logger.error()` or `logger.warning()`
- Methods return boolean or raise exceptions explicitly
- Example from `src/auth.py`:
  ```python
  try:
      response = await client.post(...)
      response.raise_for_status()
  except httpx.HTTPStatusError as e:
      logger.error(f"HTTP error during login: {e.response.status_code}")
      return False
  except httpx.RequestError as e:
      logger.error(f"Network error during login: {str(e)}")
      return False
  except Exception as e:
      logger.error(f"Unexpected error: {str(e)}")
      return False
  ```
- Async functions return `bool` or `Dict[str, Any]` with explicit error handling
- Property checks before operations: `if not self.is_authenticated:` before attempting to access resources

## Logging

**Framework:** Loguru (`from loguru import logger`)

**Patterns:**
- Configuration in `src/utils/logger.py` with `setup_logger()` function
- Log levels: DEBUG for internal details, INFO for flow tracking, WARNING for conditions, ERROR for failures
- Context-rich messages include operation details: `f"Calling tool: {name} with arguments: {arguments}"`
- Error logging includes both user-friendly message and debug details:
  ```python
  logger.error(f"HTTP {e.response.status_code} error for {endpoint}")
  logger.debug(f"Response: {e.response.text}")
  ```
- Logger configured with timestamps, level, caller info: `<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>`

## Comments

**When to Comment:**
- Module-level docstring required: all files start with triple-quoted module docstring
- Class docstrings: Required for all classes with purpose and responsibility
- Function docstrings: Required for all public functions, including async functions
- Inline comments sparse; code is self-documenting through naming

**JSDoc/TSDoc:**
- Standard Python docstring format (no JSDoc/TSDoc; this is Python)
- Docstring structure includes:
  - One-line summary followed by blank line
  - Extended description if needed
  - Args section with type and description: `email: Kledo account email`
  - Returns section with type and description: `Returns: True if login successful, False otherwise`
  - Example from `src/auth.py`:
    ```python
    def __init__(self, email: str, password: str, base_url: str, app_client: str = "android"):
        """
        Initialize authenticator.

        Args:
            email: Kledo account email
            password: Kledo account password
            base_url: API base URL
            app_client: Device type (android/ios)
        """
    ```

## Function Design

**Size:**
- Functions typically 10-50 lines for tool operations
- Long functions refactored into helper functions with leading underscore
- Async request function (`_request()` in `src/kledo_client.py`) is ~70 lines but self-contained with clear sections

**Parameters:**
- Explicit parameters over kwargs for clarity
- Type hints on all parameters: `name: str`, `arguments: Dict[str, Any]`
- Default values for optional parameters: `per_page: int = 50`, `force_refresh: bool = False`
- No variadic args; specific parameter lists maintained
- Example signature: `async def get(self, category: str, name: str, params: Optional[Dict[str, Any]] = None, ...)`

**Return Values:**
- Explicit return types in function signatures: `-> bool`, `-> str`, `-> Dict[str, Any]`
- Async functions return awaitable types: `async def login() -> bool`
- Consistent return type across similar functions
- Example: tool handlers return `str` for display: `async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:`

## Module Design

**Exports:**
- Public API via module-level functions: `get_tools()` and `handle_tool()` in each tool module
- Tool modules in `src/tools/` export consistent interface for tool registration
- Utilities exported from `src/utils/helpers.py`: `calculate_hash()`, `format_currency()`, `parse_date_range()`, `safe_get()`, etc.
- Configuration helpers in `src/utils/logger.py`: `setup_logger()`, `get_logger()`

**Barrel Files:**
- `src/tools/__init__.py` imports submodules: `from . import financial, invoices, orders, products, contacts, deliveries, utilities`
- `src/models/__init__.py` exists but appears minimal (for future model definitions)
- `src/utils/__init__.py` minimal; direct imports used instead

---

*Convention analysis: 2026-01-21*
