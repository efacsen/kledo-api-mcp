"""
Order tools for Kledo MCP Server
"""

from typing import Any

from ..kledo_client import KledoAPIClient
from ..utils.helpers import format_currency, parse_date_range, safe_get


async def _list_orders(args: dict[str, Any], client: KledoAPIClient) -> str:
    """List orders (sales or purchase based on type parameter)."""
    order_type = args.get("type")

    if not order_type:
        return "Error: type parameter is required. Must be 'sales' or 'purchase'."

    if order_type not in ["sales", "purchase"]:
        return f"Error: Invalid type '{order_type}'. Must be 'sales' or 'purchase'."

    # Delegate to appropriate handler
    if order_type == "sales":
        return await _list_sales_orders(args, client)
    else:
        return await _list_purchase_orders(args, client)


async def _list_sales_orders(args: dict[str, Any], client: KledoAPIClient) -> str:
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
                "per_page": 50,
            },
            cache_category="orders",
        )

        result = ["# Sales Orders\n"]

        orders = safe_get(data, "data.data", [])

        if not orders:
            result.append("No sales orders found.")
            return "\n".join(result)

        result.append(f"**Total Found**: {len(orders)}\n")

        total_amount = sum(safe_get(order, "amount_after_tax", 0) for order in orders)
        result.append(f"**Total Amount**: {format_currency(total_amount)}\n")

        result.append("\n## Orders:\n")

        # Status mapping
        status_map = {5: "Open", 6: "Partial", 7: "Converted"}

        for order in orders[:20]:
            order_number = safe_get(order, "ref_number", "N/A")
            customer = safe_get(order, "contact.name", "Unknown")
            date = safe_get(order, "trans_date", "")
            amount = safe_get(order, "amount_after_tax", 0)
            status_id = safe_get(order, "status_id", 0)
            status = status_map.get(status_id, f"Status-{status_id}")

            result.append(f"### {order_number}")
            order_id = safe_get(order, "id")          # numeric ID for order_get
            if order_id is not None:
                result.append(f"- **ID**: {order_id}")
            result.append(f"- **Customer**: {customer}")
            result.append(f"- **Date**: {date}")
            result.append(f"- **Amount**: {format_currency(amount)}")
            result.append(f"- **Status**: {status}\n")

        if len(orders) > 20:
            result.append(f"... and {len(orders) - 20} more orders")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching sales orders: {str(e)}"


async def _get_order(args: dict[str, Any], client: KledoAPIClient) -> str:
    """Get order detail."""
    order_id = args.get("order_id")

    if not order_id:
        return "Error: order_id is required"

    try:
        data = await client.get(
            "orders", "detail", path_params={"id": order_id}, cache_category="orders"
        )

        order = safe_get(data, "data.data")
        if not order:
            return f"Order #{order_id} not found"

        result = ["# Sales Order Details\n"]

        # Status mapping
        status_map = {5: "Open", 6: "Partial", 7: "Converted"}
        status_id = safe_get(order, "status_id", 0)
        status = status_map.get(status_id, f"Status-{status_id}")

        result.append(f"**Order Number**: {safe_get(order, 'ref_number', 'N/A')}")
        result.append(f"**Customer**: {safe_get(order, 'contact.name', 'Unknown')}")
        result.append(f"**Date**: {safe_get(order, 'trans_date', '')}")
        result.append(f"**Status**: {status}\n")

        subtotal = safe_get(order, "subtotal", 0)
        total = safe_get(order, "amount_after_tax", 0)

        result.append(f"**Subtotal**: {format_currency(subtotal)}")
        result.append(f"**Total**: {format_currency(total)}\n")

        # Line items (Kledo API returns "items" in detail responses; fall back to "detail")
        items = safe_get(order, "items", []) or safe_get(order, "detail", [])
        if items:
            result.append("\n## Items:\n")
            for item in items:
                desc = safe_get(item, "desc", "Unknown item")
                qty = safe_get(item, "qty", 0)
                price = safe_get(item, "price", 0)
                amount = safe_get(item, "amount", 0)

                result.append(f"- **{desc}**")
                result.append(
                    f"  - Qty: {qty} × {format_currency(price)} = {format_currency(amount)}"
                )

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching order details: {str(e)}"


async def _list_purchase_orders(args: dict[str, Any], client: KledoAPIClient) -> str:
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
                "per_page": 50,
            },
            cache_category="orders",
        )

        result = ["# Purchase Orders\n"]

        orders = safe_get(data, "data.data", [])

        if not orders:
            result.append("No purchase orders found.")
            return "\n".join(result)

        result.append(f"**Total Found**: {len(orders)}\n")

        total_amount = sum(safe_get(order, "amount_after_tax", 0) for order in orders)
        result.append(f"**Total Amount**: {format_currency(total_amount)}\n")

        result.append("\n## Purchase Orders:\n")

        # Status mapping
        status_map = {5: "Open", 6: "Partial", 7: "Converted"}

        for order in orders[:20]:
            order_number = safe_get(order, "ref_number", "N/A")
            vendor = safe_get(order, "contact.name", "Unknown")
            date = safe_get(order, "trans_date", "")
            amount = safe_get(order, "amount_after_tax", 0)
            status_id = safe_get(order, "status_id", 0)
            status = status_map.get(status_id, f"Status-{status_id}")

            result.append(f"### {order_number}")
            order_id = safe_get(order, "id")          # numeric ID for order_get
            if order_id is not None:
                result.append(f"- **ID**: {order_id}")
            result.append(f"- **Vendor**: {vendor}")
            result.append(f"- **Date**: {date}")
            result.append(f"- **Amount**: {format_currency(amount)}")
            result.append(f"- **Status**: {status}\n")

        if len(orders) > 20:
            result.append(f"... and {len(orders) - 20} more orders")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching purchase orders: {str(e)}"
