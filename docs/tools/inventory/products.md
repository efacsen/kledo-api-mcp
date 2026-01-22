# Product Tools

Tools for managing products in Kledo. Products represent items in your inventory that can be sold or purchased.

## product_list

List products with optional search and filtering. Shows product prices and inventory.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| search | string | No | Search by product name, code/SKU, or description |
| include_inventory | boolean | No | Include warehouse inventory quantities (default: false) |
| per_page | integer | No | Results per page (default: 50) |

### Example

**Request:**
```json
{
  "search": "laptop",
  "include_inventory": true,
  "per_page": 20
}
```

**Response:** Returns a list of products with:
- Product name
- SKU/code
- Sell price
- Category
- Stock quantity (if include_inventory is true)

**Related Entity:** [Product](../../entities/product.md)

---

## product_get_detail

Get detailed information about a specific product including pricing and inventory.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| product_id | integer | **Yes** | Product ID |

### Example

**Request:**
```json
{
  "product_id": 123
}
```

**Response:** Returns complete product details including:
- Name, SKU/code, category
- Description
- Sell price and cost price
- Current stock quantity
- Stock by warehouse breakdown

**Related Entity:** [Product](../../entities/product.md)

---

## product_search_by_sku

Search for a product by its SKU/code and get current price.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| sku | string | **Yes** | Product SKU/code |

### Example

**Request:**
```json
{
  "sku": "LAPTOP-001"
}
```

**Response:** Returns product information:
- Name
- SKU
- Current price
- Cost
- Stock quantity
- Category

**Related Entity:** [Product](../../entities/product.md)

---

## See Also

- [Deliveries](deliveries.md) - Product shipments
- [Sales Invoices](../sales/invoices.md) - Product sales
- [Product Entity](../../entities/product.md) - Data model reference
