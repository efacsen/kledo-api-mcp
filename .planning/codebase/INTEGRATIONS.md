# External Integrations

**Analysis Date:** 2026-01-21

## APIs & External Services

**Kledo CRM/Finance API:**
- Service: Kledo API (https://api.kledo.com/api/v1) - Primary business data source
  - SDK/Client: Custom wrapper `KledoAPIClient` in `src/kledo_client.py`
  - Auth: Bearer token from `/authentication/singleLogin` endpoint
  - Auth module: `src/auth.py` with `KledoAuthenticator` class

**Kledo API Endpoint Categories:**
The system integrates with 11+ endpoint categories as defined in `config/endpoints.yaml`:
- **Authentication**: `/authentication/singleLogin`, `/authentication/logout`
- **Financial Reports**: `/reportings/activity-team`, `/reportings/profit-loss`, `/reportings/balance-sheet`, `/reportings/cash-flow`, `/reportings/sales-by-contact`, `/reportings/purchase-by-contact`
- **Invoices**: `/finance/invoices`, `/finance/invoices/{id}`, `/finance/invoices/totals`, `/finance/invoices/availableMemos`
- **Purchase Invoices**: `/finance/purchaseInvoices`, `/finance/purchaseInvoices/{id}`, `/finance/purchaseInvoices/totals`
- **Orders**: `/finance/orders`, `/finance/orders/{id}`, `/finance/orders/totals`
- **Purchase Orders**: `/finance/purchaseOrders`, `/finance/purchaseOrders/{id}`, `/finance/purchaseOrders/totals`
- **Products**: `/finance/products`, `/finance/products/{id}`, `/finance/products/suggestion`, `/finance/productCategories`
- **Contacts**: `/finance/contacts`, `/finance/contacts/{id}`, `/finance/contacts/{id}/transactions`, `/finance/contacts/{id}/invoiceStatus`, `/finance/contacts/{id}/purchaseStatus`, `/finance/contactGroups`
- **Deliveries**: `/finance/deliveries`, `/finance/deliveries/{id}`, `/finance/deliveries/totals`
- **Purchase Deliveries**: `/finance/purchaseDeliveries`, `/finance/purchaseDeliveries/{id}`
- **Bank & Payments**: `/finance/bankTrans`, `/finance/bankTrans/{id}`, `/finance/bankTrans/totals`, `/finance/bank/balances`, `/banks`, `/banks/{id}`
- **Accounts**: `/finance/accounts`, `/finance/accounts/{id}`, `/finance/accounts/suggestion`
- **Supporting Data**: `/finance/units`, `/finance/tags`, `/finance/fees`, `/warehouses`, `/locations`

## Data Storage

**Databases:**
- Not applicable - This is a read-only API client with no persistent storage
- All data is fetched from Kledo API on demand

**File Storage:**
- Local filesystem only - Log files stored in `logs/` directory (configured via `LOG_FILE` env var)

**Caching:**
- In-memory cache with TTL management: `KledoCache` class in `src/cache.py`
- Cache configuration: `config/cache_config.yaml` defines 4 tiers:
  - **Master Data** (Products, Contacts, Accounts, Units, Tags, Config): 2-8 hour TTL
  - **Transactional** (Invoices, Orders, Deliveries, Expenses): 15-30 minute TTL
  - **Analytical** (Reports, Totals, Summaries, Dashboard): 1 hour TTL
  - **Real-time** (Bank Balance, Stock Levels): 5-10 minute TTL
- Cache settings: Max 1000 items, cleanup every 5 minutes

## Authentication & Identity

**Auth Provider:**
- Custom implementation with Kledo API
  - Implementation: `src/auth.py` - `KledoAuthenticator` class
  - Login endpoint: POST `/authentication/singleLogin`
  - Logout endpoint: POST `/authentication/logout`
  - Token type: Bearer token
  - Token storage: In-memory, expires based on `expires_in` from login response (default 24 hours)

**Auth Flow:**
1. User provides credentials via environment variables: `KLEDO_EMAIL`, `KLEDO_PASSWORD`
2. Server calls `/authentication/singleLogin` with credentials
3. Receives access token and expiry time
4. Token stored in `KledoAuthenticator._access_token` with expiry tracking
5. All subsequent API calls use `Authorization: Bearer {token}` header
6. Token automatically refreshed when expired via `ensure_authenticated()`

**Headers Required:**
- `Authorization: Bearer {access_token}` - For authenticated API calls
- `app-client: android` (or configurable via `KLEDO_APP_CLIENT`) - Device identifier
- `Content-Type: application/json` - For request bodies

## Monitoring & Observability

**Error Tracking:**
- None - Application logs errors but does not send to external service

**Logs:**
- Approach: File-based logging via loguru
  - Configured via `LOG_LEVEL` env var (default: INFO)
  - Output file: Configured via `LOG_FILE` env var (default: `logs/kledo-mcp.log`)
  - Handler: `src/utils/logger.py` sets up loguru with custom format

**Logging Strategy:**
- Authentication events logged at `INFO` level
- API request errors logged at `ERROR` level with HTTP status codes
- Cache operations logged at `DEBUG` level
- Tool execution tracked with call/completion logging

## CI/CD & Deployment

**Hosting:**
- Local execution: Standalone Python process
- Claude Desktop integration: Configured via `claude_desktop_config.json`
- Command: `python -m src.server`

**CI Pipeline:**
- None detected - No GitHub Actions or CI service configured

## Environment Configuration

**Required env vars:**
- `KLEDO_EMAIL` - Kledo account email (REQUIRED)
- `KLEDO_PASSWORD` - Kledo account password (REQUIRED)
- `KLEDO_BASE_URL` - API base URL (default: https://api.kledo.com/api/v1)
- `KLEDO_APP_CLIENT` - Device type (default: android)
- `CACHE_ENABLED` - Enable/disable caching (default: true)
- `CACHE_DEFAULT_TTL` - Default cache TTL in seconds (default: 1800 = 30 minutes)
- `LOG_LEVEL` - Logging level (default: INFO)
- `LOG_FILE` - Log file path (default: logs/kledo-mcp.log)
- `MCP_SERVER_NAME` - MCP server name (default: kledo-crm)
- `MCP_SERVER_VERSION` - MCP server version (default: 1.0.0)

**Secrets location:**
- Environment variables (recommended approach)
- For Claude Desktop: Configured in `claude_desktop_config.json` with env section
- Development: Use `.env` file (copied from `.env.example`)

## Webhooks & Callbacks

**Incoming:**
- None - This is a read-only client, no webhook endpoints exposed

**Outgoing:**
- None - No callbacks sent to external services

---

*Integration audit: 2026-01-21*
