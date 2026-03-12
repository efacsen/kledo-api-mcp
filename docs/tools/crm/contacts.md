# Contact Tools

Tools for managing contacts in Kledo. Contacts represent customers and vendors in your business.

## contact_list

List customers and vendors with optional search and filtering.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| search | string | No | Search by name, email, phone, or company |
| type_id | integer | No | Filter by type (1=Customer, 2=Vendor, 3=Both) |
| per_page | integer | No | Results per page (default: 50) |

### Example

**Request:**
```json
{
  "search": "Acme",
  "type_id": 1,
  "per_page": 20
}
```

**Response:** Returns a list of contacts with:
- Name
- Company
- Type (Customer/Vendor)
- Email
- Phone

**Related Entity:** [Contact](../../entities/contact.md)

---

## contact_get

Get detailed information or transaction history for a specific contact. Use the `view` parameter to control output.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| contact_id | integer | **Yes** | Contact ID |
| view | string | No | Output mode: `"detail"` (default) or `"transactions"` |

### Example — Detail View

**Request:**
```json
{
  "contact_id": 123,
  "view": "detail"
}
```

**Response:** Returns complete contact details including:
- Name and company
- Type (Customer/Vendor)
- Email and phone
- Address
- Financial summary (receivables, payables)

### Example — Transactions View

**Request:**
```json
{
  "contact_id": 123,
  "view": "transactions"
}
```

**Response:** Returns transaction history including:
- Total transaction count
- Total amount
- Recent transactions with type, number, date, amount, and status

**Related Entity:** [Contact](../../entities/contact.md)

---

## See Also

- [Sales Invoices](../sales/invoices.md) - Customer invoices
- [Purchase Invoices](../purchases/invoices.md) - Vendor bills
- [Financial Reports](../finance/reports.md) - Sales and purchase summaries
- [Contact Entity](../../entities/contact.md) - Data model reference
