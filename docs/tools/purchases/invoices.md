# Purchase Invoice Tools

Tools for managing purchase invoices (vendor bills) in Kledo. Purchase invoices represent bills received from vendors for goods or services.

## invoice_list_purchase

List purchase invoices (bills from vendors) with optional filtering.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| search | string | No | Search term |
| contact_id | integer | No | Filter by vendor ID |
| status_id | integer | No | Filter by status |
| date_from | string | No | Start date |
| date_to | string | No | End date |
| per_page | integer | No | Results per page (default: 50) |

### Example

**Request:**
```json
{
  "contact_id": 456,
  "status_id": 2,
  "date_from": "2024-01-01"
}
```

**Response:** Returns a list of purchase invoices with:
- Invoice number
- Vendor name
- Date
- Total amount
- Status

**Related Entity:** [Invoice](../../entities/invoice.md)

---

## See Also

- [Sales Invoices](../sales/invoices.md) - Customer invoices
- [Purchase Orders](orders.md) - Pre-invoice purchase orders
- [Invoice Entity](../../entities/invoice.md) - Data model reference
