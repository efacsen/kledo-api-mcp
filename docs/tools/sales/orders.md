# Sales Order Tools

Tools for managing sales orders in Kledo. Sales orders represent customer orders before they are invoiced.

## order_list

List sales orders with optional filtering. Use `type="sales"` for sales orders.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | **Yes** | Order type: `"sales"` or `"purchase"` |
| search | string | No | Search term |
| contact_id | integer | No | Filter by customer ID |
| status_id | integer | No | Filter by status |
| date_from | string | No | Start date |
| date_to | string | No | End date |

### Example

**Request:**
```json
{
  "type": "sales",
  "contact_id": 123,
  "date_from": "2024-01-01"
}
```

**Response:** Returns a list of sales orders with order number, customer name, date, total amount, and status.

**Related Entity:** [Order](../../entities/order.md)

---

## order_get

Get detailed information about a specific sales order.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| order_id | integer | **Yes** | Sales order ID |

### Example

**Request:**
```json
{
  "order_id": 789
}
```

**Response:** Returns complete order details including:
- Order number and date
- Customer information
- Line items with product, quantity, price, amount
- Subtotal and total
- Order status

**Related Entity:** [Order](../../entities/order.md)

---

## See Also

- [Sales Invoices](invoices.md) - Convert orders to invoices
- [Purchase Orders](../purchases/orders.md) - Vendor orders
- [Order Entity](../../entities/order.md) - Data model reference
