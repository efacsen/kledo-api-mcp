# Sales Invoice Tools

Tools for managing sales invoices in Kledo. Sales invoices represent bills sent to customers for goods or services.

## invoice_list

List sales invoices with optional filtering by customer, status, date range, or search term. Use `type="sales"` for sales invoices.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | **Yes** | Invoice type: `"sales"` or `"purchase"` |
| search | string | No | Search term for invoice number or details |
| contact_id | integer | No | Filter by customer ID |
| status_id | integer | No | Filter by status (1=Draft, 2=Pending, 3=Paid, etc.) |
| date_from | string | No | Start date (YYYY-MM-DD or shortcuts like 'last_month') |
| date_to | string | No | End date (YYYY-MM-DD) |
| per_page | integer | No | Results per page (default: 50) |

### Example

**Request:**
```json
{
  "type": "sales",
  "contact_id": 123,
  "status_id": 2,
  "date_from": "2024-01-01",
  "date_to": "2024-01-31"
}
```

**Response:** Returns a list of invoices with invoice number, customer name, date, total amount, paid amount, and status.

**Related Entity:** [Invoice](../../entities/invoice.md)

---

## invoice_get

Get detailed information about a specific invoice including line items.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| invoice_id | integer | **Yes** | Invoice ID |

### Example

**Request:**
```json
{
  "invoice_id": 456
}
```

**Response:** Returns complete invoice details including:
- Invoice number, date, due date
- Customer information
- Line items with product, quantity, price, amount
- Subtotal, tax, total
- Payment status and amount paid

**Related Entity:** [Invoice](../../entities/invoice.md)

---

## invoice_summarize

Get summary totals or breakdowns for invoices. Use the `view` parameter to control output.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| view | string | **Yes** | Summary type: `"totals"`, `"by_customer"`, or `"by_vendor"` |
| date_from | string | No | Start date filter |
| date_to | string | No | End date filter |

### Example

**Request:**
```json
{
  "view": "totals",
  "date_from": "2024-01-01",
  "date_to": "2024-12-31"
}
```

**Response:** Returns invoice totals including:
- Total invoice count
- Total amount invoiced
- Total amount paid
- Outstanding balance
- Overdue amount

**Related Entity:** [Invoice](../../entities/invoice.md)

---

## See Also

- [Purchase Invoices](../purchases/invoices.md) - Vendor bills
- [Sales Orders](orders.md) - Pre-invoice sales orders
- [Invoice Entity](../../entities/invoice.md) - Data model reference
