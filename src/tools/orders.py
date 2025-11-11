"""
Order tools for Kledo MCP Server
"""
from typing import Any, Dict
from mcp.types import Tool

from ..kledo_client import KledoAPIClient
from ..utils.helpers import parse_date_range, format_currency, safe_get


def get_tools() -> list[Tool]:
    """Get list of order tools."""
    return [
        Tool(
            name="order_list_sales",
            description="List sales orders with optional filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search term"
                    },
                    "contact_id": {
                        "type": "integer",
                        "description": "Filter by customer ID"
                    },
                    "status_id": {
                        "type": "integer",
                        "description": "Filter by status"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="order_get_detail",
            description="Get detailed information about a specific sales order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "Sales order ID"
                    }
                },
                "required": ["order_id"]
            }
        ),
        Tool(
            name="order_list_purchase",
            description="List purchase orders with optional filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search term"
                    },
                    "contact_id": {
                        "type": "integer",
                        "description": "Filter by vendor ID"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date"
                    }
                },
                "required": []
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:
    """Handle order tool calls."""
    if name == "order_list_sales":
        return await _list_sales_orders(arguments, client)
    elif name == "order_get_detail":
        return await _get_order_detail(arguments, client)
    elif name == "order_list_purchase":
        return await _list_purchase_orders(arguments, client)
    else:
        return f"Unknown order tool: {name}"


async def _list_sales_orders(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """List sales orders."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        data = await client.get(
            "orders",
            "list",
            params={
                "search": args.get("search"),
                "contact_id": args.get("contact_id"),
                "status_id": args.get("status_id"),
                "date_from": date_from,
                "date_to": date_to,
                "per_page": 50
            },
            cache_category="orders"
        )

        result = ["# Sales Orders\n"]

        orders = safe_get(data, "data.data", [])

        if not orders:
            result.append("No sales orders found.")
            return "\n".join(result)

        result.append(f"**Total Found**: {len(orders)}\n")

        total_amount = sum(safe_get(order, "grand_total", 0) for order in orders)
        result.append(f"**Total Amount**: {format_currency(total_amount)}\n")

        result.append("\n## Orders:\n")

        for order in orders[:20]:
            order_number = safe_get(order, "trans_number", "N/A")
            customer = safe_get(order, "contact_name", "Unknown")
            date = safe_get(order, "trans_date", "")
            amount = safe_get(order, "grand_total", 0)
            status = safe_get(order, "status_name", "Unknown")

            result.append(f"### {order_number}")
            result.append(f"- **Customer**: {customer}")
            result.append(f"- **Date**: {date}")
            result.append(f"- **Amount**: {format_currency(amount)}")
            result.append(f"- **Status**: {status}\n")

        if len(orders) > 20:
            result.append(f"... and {len(orders) - 20} more orders")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching sales orders: {str(e)}"


async def _get_order_detail(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get order detail."""
    order_id = args.get("order_id")

    if not order_id:
        return "Error: order_id is required"

    try:
        data = await client.get(
            "orders",
            "detail",
            path_params={"id": order_id},
            cache_category="orders"
        )

        order = safe_get(data, "data.data")
        if not order:
            return f"Order #{order_id} not found"

        result = ["# Sales Order Details\n"]

        result.append(f"**Order Number**: {safe_get(order, 'trans_number', 'N/A')}")
        result.append(f"**Customer**: {safe_get(order, 'contact_name', 'Unknown')}")
        result.append(f"**Date**: {safe_get(order, 'trans_date', '')}")
        result.append(f"**Status**: {safe_get(order, 'status_name', 'Unknown')}\n")

        subtotal = safe_get(order, "subtotal", 0)
        total = safe_get(order, "grand_total", 0)

        result.append(f"**Subtotal**: {format_currency(subtotal)}")
        result.append(f"**Total**: {format_currency(total)}\n")

        # Line items
        items = safe_get(order, "detail", [])
        if items:
            result.append("\n## Items:\n")
            for item in items:
                desc = safe_get(item, "desc", "Unknown item")
                qty = safe_get(item, "qty", 0)
                price = safe_get(item, "price", 0)
                amount = safe_get(item, "amount", 0)

                result.append(f"- **{desc}**")
                result.append(f"  - Qty: {qty} × {format_currency(price)} = {format_currency(amount)}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching order details: {str(e)}"


async def _list_purchase_orders(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """List purchase orders."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        data = await client.get(
            "purchase_orders",
            "list",
            params={
                "search": args.get("search"),
                "contact_id": args.get("contact_id"),
                "date_from": date_from,
                "date_to": date_to,
                "per_page": 50
            },
            cache_category="orders"
        )

        result = ["# Purchase Orders\n"]

        orders = safe_get(data, "data.data", [])

        if not orders:
            result.append("No purchase orders found.")
            return "\n".join(result)

        result.append(f"**Total Found**: {len(orders)}\n")

        total_amount = sum(safe_get(order, "grand_total", 0) for order in orders)
        result.append(f"**Total Amount**: {format_currency(total_amount)}\n")

        result.append("\n## Purchase Orders:\n")

        for order in orders[:20]:
            order_number = safe_get(order, "trans_number", "N/A")
            vendor = safe_get(order, "contact_name", "Unknown")
            date = safe_get(order, "trans_date", "")
            amount = safe_get(order, "grand_total", 0)

            result.append(f"### {order_number}")
            result.append(f"- **Vendor**: {vendor}")
            result.append(f"- **Date**: {date}")
            result.append(f"- **Amount**: {format_currency(amount)}\n")

        if len(orders) > 20:
            result.append(f"... and {len(orders) - 20} more orders")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching purchase orders: {str(e)}"
