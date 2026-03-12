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

## product_get

Get detailed information about a specific product, or look up a product by SKU.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| product_id | integer | No | Product ID (use when looking up by ID) |
| sku | string | No | Product SKU/code (use when looking up by SKU) |

Either `product_id` or `sku` must be provided.

### Example — By ID

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

### Example — By SKU

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
