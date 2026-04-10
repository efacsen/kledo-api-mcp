# Kledo API Mapping

This document maps Kledo API endpoints to MCP tools and provides usage examples.

---

## Field Glossary — Invoice (`GET /finance/invoices`)

Critical fields and their meaning in PT CSS business context:

| Field | Type | Meaning | Notes |
|-------|------|---------|-------|
| `id` | int | Invoice record ID | Internal Kledo ID |
| `contact_id` | int | Customer ID | References `GET /finance/contacts/{id}` |
| `sales_id` | int | Sales rep's Kledo user ID | **Native field.** 6-digit number. Same as `sales_person.id` |
| `owner_id` | int | Who created the invoice | Can differ from `sales_id` — e.g. admin inputs invoice on behalf of a sales rep |
| `status_id` | int | Payment status | 1=Unpaid, 2=Partial, 3=Paid |
| `amount_after_tax` | int | Total invoice value incl. tax | |
| `due` | int | Remaining unpaid amount | 0 if fully paid |
| `subtotal` | int | Net sales before tax | = "Penjualan Neto" |

### `sales_id` vs `sales_person` object

Both refer to the same person and same ID value:

```json
"sales_id": 352181,
"sales_person": {
  "id": 352181,
  "name": "Elmo Abu Abdillah"
}
```

`sales_person` is an expanded object returned by Kledo — it's not a separate concept, just `sales_id` with the name joined in. When filtering by sales rep, use `sales_id`.

### `sales_id` vs `owner_id`

```json
"owner_id": 218933,   ← Meka (created the invoice)
"sales_id": 352181,   ← Elmo (assigned sales rep)
```

These can be different people. For access control and attribution, always use `sales_id`, not `owner_id`.

---

## Kledo Users

### List PT CSS Employees
- **Endpoint**: `GET /users`
- **Returns**: All Kledo user accounts for PT CSS
- **Key field**: `id` — the 6-digit user ID
- **Usage**: This `id` is the same value as `sales_id` in invoices and `sales_id` in orders

**This is how CSS Agent identifies which sales rep owns which invoice:**
```
CSS Agent user.kledo_user_id  ==  invoice.sales_id  ==  order.sales_id
```

No MCP tool wraps this endpoint currently — used internally for user setup.

---

## Authentication

### Login
- **Endpoint**: `POST /authentication/singleLogin`
- **Purpose**: Obtain access token
- **Handled by**: `KledoAuthenticator.login()`
- **Automatic**: Yes (on server start)

### Logout
- **Endpoint**: `POST /authentication/logout`
- **Handled by**: `KledoAuthenticator.logout()`
- **Manual**: Only on explicit cleanup

---

## Financial Reports

### Sales Summary by Contact
- **Tool**: `financial_summary` (with `type="sales"`)
- **Endpoint**: `GET /reportings/sales-by-contact`
- **Parameters**:
  - `date_from` (YYYY-MM-DD)
  - `date_to` (YYYY-MM-DD)
  - `contact_id` (optional)
- **Cache**: 1 hour
- **Example**:
  ```
  "Who were my top customers in October 2024?"
  ```

### Purchase Summary by Vendor
- **Tool**: `financial_summary` (with `type="purchase"`)
- **Endpoint**: `GET /reportings/purchase-by-contact`
- **Parameters**:
  - `date_from` (YYYY-MM-DD)
  - `date_to` (YYYY-MM-DD)
  - `contact_id` (optional)
- **Cache**: 1 hour
- **Example**:
  ```
  "Show me total purchases by vendor for Q4 2024"
  ```

### Bank Balances
- **Tool**: `financial_balances`
- **Endpoint**: `GET /finance/bank/balances`
- **Parameters**: None
- **Cache**: 5 minutes (real-time tier)
- **Example**:
  ```
  "What's our current bank balance?"
  ```

---

## Invoices

### List Sales Invoices
- **Tool**: `invoice_list` (with `type="sales"`)
- **Endpoint**: `GET /finance/invoices`
- **Parameters**:
  - `search` - Search term
  - `contact_id` - Filter by customer
  - `status_id` - Filter by status
  - `date_from` / `date_to` - Date range
  - `per_page` - Results per page (default: 50)
- **Cache**: 30 minutes
- **Example**:
  ```
  "Show me unpaid invoices from last month"
  ```

### Get Invoice Detail
- **Tool**: `invoice_get`
- **Endpoint**: `GET /finance/invoices/{id}`
- **Parameters**:
  - `invoice_id` (required)
- **Cache**: 30 minutes
- **Example**:
  ```
  "Show me details for invoice #INV-1234"
  ```

### Invoice Totals
- **Tool**: `invoice_summarize` (with `view="totals"`)
- **Endpoint**: `GET /finance/invoices/totals`
- **Parameters**:
  - `date_from` / `date_to` - Date range
- **Cache**: 30 minutes
- **Example**:
  ```
  "What's the total outstanding receivables?"
  ```

### List Purchase Invoices
- **Tool**: `invoice_list` (with `type="purchase"`)
- **Endpoint**: `GET /finance/purchaseInvoices`
- **Parameters**: Same as sales invoices
- **Cache**: 30 minutes
- **Example**:
  ```
  "Show me purchase invoices from vendor ABC"
  ```

---

## Orders

### List Sales Orders
- **Tool**: `order_list` (with `type="sales"`)
- **Endpoint**: `GET /finance/orders`
- **Parameters**:
  - `search`
  - `contact_id`
  - `status_id`
  - `date_from` / `date_to`
- **Cache**: 30 minutes
- **Example**:
  ```
  "Show me pending sales orders"
  ```

### Get Order Detail
- **Tool**: `order_get`
- **Endpoint**: `GET /finance/orders/{id}`
- **Parameters**:
  - `order_id` (required)
- **Cache**: 30 minutes
- **Example**:
  ```
  "Show details for order #SO-5678"
  ```

### List Purchase Orders
- **Tool**: `order_list` (with `type="purchase"`)
- **Endpoint**: `GET /finance/purchaseOrders`
- **Parameters**: Same as sales orders
- **Cache**: 30 minutes
- **Example**:
  ```
  "List all open purchase orders"
  ```

---

## Products

### List Products
- **Tool**: `product_list`
- **Endpoint**: `GET /finance/products`
- **Parameters**:
  - `search` - Search by name/code/description
  - `include_warehouse_qty` - Include inventory (0/1)
  - `per_page` - Results per page
- **Cache**: 2 hours
- **Example**:
  ```
  "Show me all products with their current prices"
  ```

### Get Product Detail
- **Tool**: `product_get`
- **Endpoint**: `GET /finance/products/{id}`
- **Parameters**:
  - `product_id` (required)
- **Cache**: 2 hours
- **Example**:
  ```
  "Show me detailed info for product #123"
  ```

### Search by SKU
- **Tool**: `product_get` (with `sku` param)
- **Endpoint**: `GET /finance/products?code={sku}`
- **Parameters**:
  - `sku` (required)
- **Cache**: 2 hours
- **Example**:
  ```
  "What's the current price for SKU-ABC-123?"
  ```

---

## Contacts (CRM)

### List Contacts
- **Tool**: `contact_list`
- **Endpoint**: `GET /finance/contacts`
- **Parameters**:
  - `search` - Search by name/email/phone
  - `type_id` - 1=Customer, 2=Vendor, 3=Both
  - `per_page`
- **Cache**: 2 hours
- **Example**:
  ```
  "Show me all active customers"
  ```

### Get Contact Detail
- **Tool**: `contact_get` (with `view="detail"`)
- **Endpoint**: `GET /finance/contacts/{id}`
- **Parameters**:
  - `contact_id` (required)
- **Cache**: 2 hours
- **Example**:
  ```
  "Show me details for customer XYZ Corp"
  ```

### Get Contact Transactions
- **Tool**: `contact_get` (with `view="transactions"`)
- **Endpoint**: `GET /finance/contacts/{id}/transactions`
- **Parameters**:
  - `contact_id` (required)
- **Cache**: 2 hours
- **Example**:
  ```
  "Show me transaction history for customer #456"
  ```

---

## Deliveries

### List Deliveries
- **Tool**: `delivery_list`
- **Endpoint**: `GET /finance/deliveries`
- **Parameters**:
  - `search`
  - `date_from` / `date_to`
  - `status_id`
- **Cache**: 15 minutes
- **Example**:
  ```
  "Show me all deliveries this week"
  ```

### Get Delivery Detail
- **Tool**: `delivery_get` (with `view="detail"`)
- **Endpoint**: `GET /finance/deliveries/{id}`
- **Parameters**:
  - `delivery_id` (required)
- **Cache**: 15 minutes
- **Example**:
  ```
  "Show me tracking info for delivery #DEL-789"
  ```

### Get Pending Deliveries
- **Tool**: `delivery_get` (with `view="pending"`)
- **Endpoint**: `GET /finance/deliveries?status_id=1`
- **Parameters**: None (filtered to pending status)
- **Cache**: 15 minutes (force refresh)
- **Example**:
  ```
  "Which orders haven't been delivered yet?"
  ```

---

## Utilities

### Clear Cache
- **Tool**: `utility_cache` (with `action="clear"`)
- **No API call** - Local operation
- **Example**:
  ```
  "Clear the cache to get fresh data"
  ```

### Get Cache Stats
- **Tool**: `utility_cache` (with `action="stats"`)
- **No API call** - Local operation
- **Returns**: Hit rate, size, hits, misses, etc.
- **Example**:
  ```
  "Show me cache performance stats"
  ```

### Test Connection
- **Tool**: `utility_test_connection`
- **Endpoint**: `GET /banks` (lightweight test)
- **Returns**: Auth status, API connectivity
- **Example**:
  ```
  "Test if we're connected to Kledo API"
  ```

---

## Common Query Parameters

Most list endpoints support these standard parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Full-text search |
| `per_page` | integer | Results per page (default: 50, max: 100) |
| `page` | integer | Page number (default: 1) |
| `date_from` | date | Start date filter (YYYY-MM-DD) |
| `date_to` | date | End date filter (YYYY-MM-DD) |
| `status_id` | integer | Filter by status |
| `contact_id` | integer | Filter by contact/customer/vendor |
| `include_archive` | integer | 0=active only, 1=include archived, 2=archived only |

---

## Status Codes

### Invoice/Order Status
- `1` - Draft
- `2` - Pending
- `3` - Paid/Completed
- `4` - Overdue
- `5` - Cancelled

### Contact Types
- `1` - Customer
- `2` - Vendor
- `3` - Both (Customer & Vendor)

### Delivery Status
- `1` - Pending
- `2` - In Transit
- `3` - Delivered
- `4` - Cancelled

---

## Date Shortcuts

Tools support natural language date shortcuts:

| Shortcut | Resolves To |
|----------|-------------|
| `today` | Current date |
| `this_month` | 1st of current month to today |
| `last_month` | Full previous calendar month |
| `this_year` | Jan 1 of current year to today |
| `last_year` | Full previous calendar year |
| `2024-10` | October 1-31, 2024 (full month) |

Example:
```
"Show me sales for last_month"
→ date_from="2024-10-01", date_to="2024-10-31"
```

---

## Response Format

All tools return markdown-formatted text:

```markdown
# Report Title

**Metadata**: Value
**Period**: Date range

## Section Header

Content and data...

### Subsection

- List item 1
- List item 2

**Summary**: Total values
```

---

## Error Responses

Tools return user-friendly error messages:

```
"Error fetching invoices: HTTP 401 - Unauthorized"
"Error: invoice_id is required"
"No invoices found matching the criteria."
```

---

## Cache Behavior

### Cache TTL by Category

| Category | TTL | Reason |
|----------|-----|--------|
| Products | 2 hours | Master data, changes rarely |
| Contacts | 2 hours | Master data |
| Invoices | 30 min | Transactional, moderate changes |
| Orders | 30 min | Transactional |
| Reports | 1 hour | Expensive queries |
| Bank Balance | 5 min | Real-time financial data |
| Deliveries | 15 min | Operational tracking |

### Force Refresh

Some tools always fetch fresh data:
- `financial_balances` (force_refresh=True)
- `delivery_get` with `view="pending"` (force_refresh=True)

### Manual Cache Control

Use `utility_cache` with `action="clear"` to invalidate all cached data.

---

## Rate Limiting

Kledo API rate limits (if any) are handled by:
1. Caching to reduce requests
2. Automatic retry with exponential backoff
3. Request timeouts (60 seconds default)

---

## Natural Language → Tool Mapping Examples

| User Query | Selected Tool | Parameters |
|------------|---------------|------------|
| "Show unpaid invoices" | `invoice_list` | `type="sales"`, `status_id=2` (Pending) |
| "Top customers this year" | `financial_summary` | `type="sales"`, `date_from=this_year` |
| "Product info for SKU-123" | `product_get` | `sku=SKU-123` |
| "Pending deliveries" | `delivery_get` | `view="pending"` |
| "Bank balance" | `financial_balances` | (none) |
| "Customer XYZ transactions" | Contact lookup → `contact_get` | `contact_id={found_id}`, `view="transactions"` |

---

## Extending the API

To add a new endpoint:

1. Add endpoint to `config/endpoints.yaml`:
   ```yaml
   new_category:
     new_endpoint: /finance/new-endpoint
   ```

2. Create tool in appropriate module:
   ```python
   Tool(
       name="category_action_target",
       description="What it does",
       inputSchema={...}
   )
   ```

3. Add handler function:
   ```python
   async def _handle_new_tool(args, client):
       data = await client.get("new_category", "new_endpoint", ...)
       return format_response(data)
   ```

4. Update this documentation

---

**API Version**: 1.0.0  
**Last Updated**: 2025-01-11  
**Total Endpoints Mapped**: ~40 of 323 available
