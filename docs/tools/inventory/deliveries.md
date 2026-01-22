# Delivery Tools

Tools for managing deliveries in Kledo. Deliveries track shipments of products to customers.

## delivery_list

List deliveries/shipments with optional filtering by date or status.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| search | string | No | Search term |
| date_from | string | No | Start date |
| date_to | string | No | End date |
| status_id | integer | No | Filter by delivery status |

### Example

**Request:**
```json
{
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "status_id": 1
}
```

**Response:** Returns a list of deliveries with:
- Delivery number
- Customer name
- Date
- Status
- Shipping company

**Related Entity:** [Delivery](../../entities/delivery.md)

---

## delivery_get_detail

Get detailed information about a specific delivery including tracking status.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| delivery_id | integer | **Yes** | Delivery ID |

### Example

**Request:**
```json
{
  "delivery_id": 456
}
```

**Response:** Returns complete delivery details including:
- Delivery number and date
- Customer information
- Shipping company and tracking number
- Shipping address
- Items being delivered with quantities
- Reference to related order/invoice
- Delivery notes

**Related Entity:** [Delivery](../../entities/delivery.md)

---

## delivery_get_pending

Get list of pending/undelivered orders that need to be shipped.

### Parameters

This tool takes no parameters.

### Example

**Request:**
```json
{}
```

**Response:** Returns a list of pending deliveries that need to be shipped, including:
- Delivery number
- Customer name
- Created date

**Related Entity:** [Delivery](../../entities/delivery.md)

---

## See Also

- [Products](products.md) - Products being delivered
- [Sales Orders](../sales/orders.md) - Orders awaiting delivery
- [Delivery Entity](../../entities/delivery.md) - Data model reference
