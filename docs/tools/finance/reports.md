# Financial Report Tools

Tools for financial reporting in Kledo. These tools provide summaries and analytics for business performance.

## financial_activity_team_report

Get team activity report for a date range. Shows what the sales/finance team has been doing.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| date_from | string | No | Start date in YYYY-MM or YYYY-MM-DD format, or use 'last_month', 'this_month', 'this_year' |
| date_to | string | No | End date in YYYY-MM or YYYY-MM-DD format (optional if using period shortcuts) |

### Example

**Request:**
```json
{
  "date_from": "last_month"
}
```

**Response:** Returns team activity data including:
- User name
- Action type
- Activity count

---

## financial_sales_summary

Get sales summary by contact for a period. Shows total sales revenue from each customer.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| date_from | string | No | Start date (YYYY-MM-DD or shortcuts like 'last_month') |
| date_to | string | No | End date (YYYY-MM-DD) |
| contact_id | integer | No | Filter by specific contact/customer ID (optional) |

### Example

**Request:**
```json
{
  "date_from": "2024-01-01",
  "date_to": "2024-12-31"
}
```

**Response:** Returns sales summary including:
- Total sales amount
- Number of customers
- Top customers ranked by revenue with invoice counts

---

## financial_purchase_summary

Get purchase summary by vendor for a period. Shows total purchase expenses from each vendor.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| date_from | string | No | Start date (YYYY-MM-DD or shortcuts) |
| date_to | string | No | End date (YYYY-MM-DD) |
| contact_id | integer | No | Filter by specific vendor ID (optional) |

### Example

**Request:**
```json
{
  "date_from": "2024-01-01",
  "date_to": "2024-12-31"
}
```

**Response:** Returns purchase summary including:
- Total purchases amount
- Number of vendors
- Top vendors ranked by spending with invoice counts

---

## financial_bank_balances

Get current balances for all bank accounts. Shows available cash across all accounts.

### Parameters

This tool takes no parameters.

### Example

**Request:**
```json
{}
```

**Response:** Returns bank account balances including:
- Account name
- Current balance
- Currency
- Total balance across all accounts

**Related Entity:** [Account](../../entities/account.md)

---

## See Also

- [Sales Invoices](../sales/invoices.md) - Source of sales data
- [Purchase Invoices](../purchases/invoices.md) - Source of purchase data
- [Contacts](../crm/contacts.md) - Customer and vendor information
