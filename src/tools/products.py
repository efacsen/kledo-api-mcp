"""
Product tools for Kledo MCP Server
"""
from typing import Any, Dict
from mcp.types import Tool

from ..kledo_client import KledoAPIClient
from ..utils.helpers import format_currency, safe_get


def get_tools() -> list[Tool]:
    """Get list of product tools."""
    return [
        Tool(
            name="product_list",
            description="List products with optional search and filtering. Shows product prices and inventory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search by product name, code/SKU, or description"
                    },
                    "include_inventory": {
                        "type": "boolean",
                        "description": "Include warehouse inventory quantities (default: false)"
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 50)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="product_get_detail",
            description="Get detailed information about a specific product including pricing and inventory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Product ID"
                    }
                },
                "required": ["product_id"]
            }
        ),
        Tool(
            name="product_search_by_sku",
            description="Search for a product by its SKU/code and get current price.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "Product SKU/code"
                    }
                },
                "required": ["sku"]
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:
    """Handle product tool calls."""
    if name == "product_list":
        return await _list_products(arguments, client)
    elif name == "product_get_detail":
        return await _get_product_detail(arguments, client)
    elif name == "product_search_by_sku":
        return await _search_by_sku(arguments, client)
    else:
        return f"Unknown product tool: {name}"


async def _list_products(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """List products."""
    try:
        data = await client.list_products(
            search=args.get("search"),
            include_warehouse_qty=args.get("include_inventory", False),
            per_page=args.get("per_page", 50)
        )

        result = ["# Products\n"]

        products = safe_get(data, "data.data", [])

        if not products:
            result.append("No products found.")
            return "\n".join(result)

        result.append(f"**Total Found**: {len(products)}\n")

        result.append("\n## Product List:\n")

        for product in products[:30]:  # Show more products
            name = safe_get(product, "name", "Unknown")
            code = safe_get(product, "code", "N/A")
            price = safe_get(product, "price", 0)
            qty = safe_get(product, "qty", 0)
            category = safe_get(product, "category_name", "Uncategorized")

            result.append(f"### {name}")
            result.append(f"- **SKU**: {code}")
            result.append(f"- **Price**: {format_currency(price)}")
            result.append(f"- **Category**: {category}")

            if args.get("include_inventory"):
                result.append(f"- **Stock**: {qty} units")

            result.append("")

        if len(products) > 30:
            result.append(f"... and {len(products) - 30} more products")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching products: {str(e)}"


async def _get_product_detail(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get product detail."""
    product_id = args.get("product_id")

    if not product_id:
        return "Error: product_id is required"

    try:
        data = await client.get(
            "products",
            "detail",
            path_params={"id": product_id},
            cache_category="products"
        )

        product = safe_get(data, "data.data")
        if not product:
            return f"Product #{product_id} not found"

        result = ["# Product Details\n"]

        result.append(f"**Name**: {safe_get(product, 'name', 'Unknown')}")
        result.append(f"**SKU/Code**: {safe_get(product, 'code', 'N/A')}")
        result.append(f"**Category**: {safe_get(product, 'category_name', 'Uncategorized')}")

        description = safe_get(product, "description")
        if description:
            result.append(f"**Description**: {description}")

        result.append("")

        # Pricing
        result.append("## Pricing:")
        result.append(f"- **Sell Price**: {format_currency(safe_get(product, 'price', 0))}")
        result.append(f"- **Cost Price**: {format_currency(safe_get(product, 'buy_price', 0))}")

        # Inventory
        qty = safe_get(product, "qty", 0)
        result.append(f"\n**Current Stock**: {qty} units")

        # Warehouse breakdown if available
        warehouses = safe_get(product, "warehouses", [])
        if warehouses:
            result.append("\n### Stock by Warehouse:")
            for wh in warehouses:
                wh_name = safe_get(wh, "name", "Unknown")
                wh_qty = safe_get(wh, "qty", 0)
                result.append(f"- {wh_name}: {wh_qty} units")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching product details: {str(e)}"


async def _search_by_sku(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Search product by SKU."""
    sku = args.get("sku")

    if not sku:
        return "Error: sku is required"

    try:
        data = await client.get(
            "products",
            "list",
            params={"code": sku},
            cache_category="products"
        )

        products = safe_get(data, "data.data", [])

        if not products:
            return f"No product found with SKU: {sku}"

        product = products[0]  # Take first match

        result = ["# Product Information\n"]

        result.append(f"**Name**: {safe_get(product, 'name', 'Unknown')}")
        result.append(f"**SKU**: {safe_get(product, 'code', 'N/A')}")
        result.append(f"**Current Price**: {format_currency(safe_get(product, 'price', 0))}")
        result.append(f"**Cost**: {format_currency(safe_get(product, 'buy_price', 0))}")
        result.append(f"**Stock**: {safe_get(product, 'qty', 0)} units")
        result.append(f"**Category**: {safe_get(product, 'category_name', 'Uncategorized')}")

        return "\n".join(result)

    except Exception as e:
        return f"Error searching product by SKU: {str(e)}"
