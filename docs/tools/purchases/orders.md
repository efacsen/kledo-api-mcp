# Purchase Order Tools

Tools for managing purchase orders in Kledo. Purchase orders represent orders placed with vendors.

## order_list (type="purchase")

List purchase orders with optional filtering. Use `type="purchase"`.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | **Yes** | Must be `"purchase"` for purchase orders |
| search | string | No | Search term |
| contact_id | integer | No | Filter by vendor ID |
| date_from | string | No | Start date |
| date_to | string | No | End date |

### Example

**Request:**
```json
{
  "type": "purchase",
  "contact_id": 789,
  "date_from": "2024-01-01"
}
```

**Response:** Returns a list of purchase orders with:
- Order number
- Vendor name
- Date
- Total amount

**Related Entity:** [Order](../../entities/order.md)

---

## See Also

- [Sales Orders](../sales/orders.md) - Customer orders
- [Purchase Invoices](invoices.md) - Convert orders to bills
- [Order Entity](../../entities/order.md) - Data model reference
