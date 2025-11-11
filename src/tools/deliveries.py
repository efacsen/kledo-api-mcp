"""
Delivery tracking tools for Kledo MCP Server
"""
from typing import Any, Dict
from mcp.types import Tool

from ..kledo_client import KledoAPIClient
from ..utils.helpers import parse_date_range, safe_get


def get_tools() -> list[Tool]:
    """Get list of delivery tools."""
    return [
        Tool(
            name="delivery_list",
            description="List deliveries/shipments with optional filtering by date or status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search term"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date"
                    },
                    "status_id": {
                        "type": "integer",
                        "description": "Filter by delivery status"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="delivery_get_detail",
            description="Get detailed information about a specific delivery including tracking status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "delivery_id": {
                        "type": "integer",
                        "description": "Delivery ID"
                    }
                },
                "required": ["delivery_id"]
            }
        ),
        Tool(
            name="delivery_get_pending",
            description="Get list of pending/undelivered orders that need to be shipped.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:
    """Handle delivery tool calls."""
    if name == "delivery_list":
        return await _list_deliveries(arguments, client)
    elif name == "delivery_get_detail":
        return await _get_delivery_detail(arguments, client)
    elif name == "delivery_get_pending":
        return await _get_pending_deliveries(arguments, client)
    else:
        return f"Unknown delivery tool: {name}"


async def _list_deliveries(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """List deliveries."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        data = await client.get(
            "deliveries",
            "list",
            params={
                "search": args.get("search"),
                "date_from": date_from,
                "date_to": date_to,
                "status_id": args.get("status_id"),
                "per_page": 50
            },
            cache_category="deliveries"
        )

        result = ["# Deliveries\n"]

        deliveries = safe_get(data, "data.data", [])

        if not deliveries:
            result.append("No deliveries found.")
            return "\n".join(result)

        result.append(f"**Total Found**: {len(deliveries)}\n")

        result.append("\n## Delivery List:\n")

        for delivery in deliveries[:20]:
            delivery_number = safe_get(delivery, "trans_number", "N/A")
            customer = safe_get(delivery, "contact_name", "Unknown")
            date = safe_get(delivery, "trans_date", "")
            status = safe_get(delivery, "status_name", "Unknown")
            shipping_company = safe_get(delivery, "shipping_company_name", "N/A")

            result.append(f"### {delivery_number}")
            result.append(f"- **Customer**: {customer}")
            result.append(f"- **Date**: {date}")
            result.append(f"- **Status**: {status}")
            result.append(f"- **Shipping**: {shipping_company}\n")

        if len(deliveries) > 20:
            result.append(f"... and {len(deliveries) - 20} more deliveries")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching deliveries: {str(e)}"


async def _get_delivery_detail(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get delivery detail."""
    delivery_id = args.get("delivery_id")

    if not delivery_id:
        return "Error: delivery_id is required"

    try:
        data = await client.get(
            "deliveries",
            "detail",
            path_params={"id": delivery_id},
            cache_category="deliveries"
        )

        delivery = safe_get(data, "data.data")
        if not delivery:
            return f"Delivery #{delivery_id} not found"

        result = ["# Delivery Details\n"]

        result.append(f"**Delivery Number**: {safe_get(delivery, 'trans_number', 'N/A')}")
        result.append(f"**Customer**: {safe_get(delivery, 'contact_name', 'Unknown')}")
        result.append(f"**Date**: {safe_get(delivery, 'trans_date', '')}")
        result.append(f"**Status**: {safe_get(delivery, 'status_name', 'Unknown')}")

        # Shipping info
        shipping_company = safe_get(delivery, "shipping_company_name")
        if shipping_company:
            result.append(f"**Shipping Company**: {shipping_company}")

        tracking_number = safe_get(delivery, "tracking_number")
        if tracking_number:
            result.append(f"**Tracking Number**: {tracking_number}")

        # Shipping address
        shipping_address = safe_get(delivery, "shipping_address")
        if shipping_address:
            result.append(f"\n**Shipping Address**: {shipping_address}")

        # Items
        items = safe_get(delivery, "detail", [])
        if items:
            result.append("\n## Items Being Delivered:\n")
            for item in items:
                desc = safe_get(item, "desc", "Unknown item")
                qty = safe_get(item, "qty", 0)
                result.append(f"- {desc} (Qty: {qty})")

        # Reference to related invoice/order
        ref_number = safe_get(delivery, "ref_number")
        if ref_number:
            result.append(f"\n**Reference**: {ref_number}")

        # Memo
        memo = safe_get(delivery, "memo")
        if memo:
            result.append(f"\n**Notes**: {memo}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching delivery details: {str(e)}"


async def _get_pending_deliveries(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get pending deliveries."""
    try:
        # Get deliveries with pending status (assuming status_id 1 or 2 is pending)
        data = await client.get(
            "deliveries",
            "list",
            params={
                "status_id": 1,  # Adjust based on Kledo's status codes
                "per_page": 100
            },
            cache_category="deliveries",
            force_refresh=True  # Get fresh data for pending items
        )

        result = ["# Pending Deliveries\n"]

        deliveries = safe_get(data, "data.data", [])

        if not deliveries:
            result.append("No pending deliveries found. All orders have been delivered!")
            return "\n".join(result)

        result.append(f"**Total Pending**: {len(deliveries)}\n")

        result.append("\n## Orders Waiting for Delivery:\n")

        for delivery in deliveries:
            delivery_number = safe_get(delivery, "trans_number", "N/A")
            customer = safe_get(delivery, "contact_name", "Unknown")
            date = safe_get(delivery, "trans_date", "")

            result.append(f"- **{delivery_number}** - {customer} (Created: {date})")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching pending deliveries: {str(e)}"
