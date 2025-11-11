"""
Financial report tools for Kledo MCP Server
"""
from typing import Any, Dict
from mcp.types import Tool
import json

from ..kledo_client import KledoAPIClient
from ..utils.helpers import parse_date_range, format_currency, safe_get


def get_tools() -> list[Tool]:
    """Get list of financial report tools."""
    return [
        Tool(
            name="financial_activity_team_report",
            description="Get team activity report for a date range. Shows what the sales/finance team has been doing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Start date in YYYY-MM or YYYY-MM-DD format, or use 'last_month', 'this_month', 'this_year'"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date in YYYY-MM or YYYY-MM-DD format (optional if using period shortcuts)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="financial_sales_summary",
            description="Get sales summary by contact for a period. Shows total sales revenue from each customer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD or shortcuts like 'last_month')"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
                    },
                    "contact_id": {
                        "type": "integer",
                        "description": "Filter by specific contact/customer ID (optional)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="financial_purchase_summary",
            description="Get purchase summary by vendor for a period. Shows total purchase expenses from each vendor.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD or shortcuts)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
                    },
                    "contact_id": {
                        "type": "integer",
                        "description": "Filter by specific vendor ID (optional)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="financial_bank_balances",
            description="Get current balances for all bank accounts. Shows available cash across all accounts.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:
    """
    Handle financial tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments
        client: Kledo API client

    Returns:
        Formatted response string
    """
    if name == "financial_activity_team_report":
        return await _activity_team_report(arguments, client)
    elif name == "financial_sales_summary":
        return await _sales_summary(arguments, client)
    elif name == "financial_purchase_summary":
        return await _purchase_summary(arguments, client)
    elif name == "financial_bank_balances":
        return await _bank_balances(arguments, client)
    else:
        return f"Unknown financial tool: {name}"


async def _activity_team_report(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get team activity report."""
    # Parse dates
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    # Handle period shortcuts
    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    # Convert to YYYY-MM format if full date provided
    if date_from and len(date_from) == 10:  # YYYY-MM-DD
        date_from = date_from[:7]  # Take only YYYY-MM
    if date_to and len(date_to) == 10:
        date_to = date_to[:7]

    try:
        data = await client.get_activity_team_report(date_from, date_to)

        # Format response
        result = ["# Team Activity Report\n"]

        if date_from:
            result.append(f"**Period**: {date_from} to {date_to or 'present'}\n")

        # Extract relevant data from response
        report_data = safe_get(data, "data.data", [])

        if not report_data:
            result.append("No activity data found for this period.")
            return "\n".join(result)

        result.append(f"\n**Total Activities**: {len(report_data)}\n")

        # Display activities
        for activity in report_data[:20]:  # Limit to first 20
            user = activity.get("user_name", "Unknown")
            action = activity.get("action", "")
            count = activity.get("count", 0)
            result.append(f"- {user}: {action} ({count} times)")

        if len(report_data) > 20:
            result.append(f"\n... and {len(report_data) - 20} more activities")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching team activity report: {str(e)}"


async def _sales_summary(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get sales summary by contact."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")
    contact_id = args.get("contact_id")

    # Handle period shortcuts
    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        data = await client.get(
            "reports",
            "sales_by_contact",
            params={
                "date_from": date_from,
                "date_to": date_to,
                "contact_id": contact_id
            },
            cache_category="reports"
        )

        result = ["# Sales Summary by Customer\n"]

        if date_from:
            result.append(f"**Period**: {date_from} to {date_to or 'present'}\n")

        sales_data = safe_get(data, "data.data", [])

        if not sales_data:
            result.append("No sales data found for this period.")
            return "\n".join(result)

        # Calculate totals
        total_sales = sum(safe_get(s, "total", 0) for s in sales_data)
        result.append(f"**Total Sales**: {format_currency(total_sales)}\n")
        result.append(f"**Number of Customers**: {len(sales_data)}\n")

        # Top customers
        result.append("\n## Top Customers:\n")
        sorted_sales = sorted(sales_data, key=lambda x: safe_get(x, "total", 0), reverse=True)

        for idx, sale in enumerate(sorted_sales[:10], 1):
            customer = safe_get(sale, "contact_name", "Unknown")
            amount = safe_get(sale, "total", 0)
            count = safe_get(sale, "count", 0)
            result.append(f"{idx}. **{customer}**: {format_currency(amount)} ({count} invoices)")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching sales summary: {str(e)}"


async def _purchase_summary(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get purchase summary by vendor."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")
    contact_id = args.get("contact_id")

    # Handle period shortcuts
    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        data = await client.get(
            "reports",
            "purchase_by_contact",
            params={
                "date_from": date_from,
                "date_to": date_to,
                "contact_id": contact_id
            },
            cache_category="reports"
        )

        result = ["# Purchase Summary by Vendor\n"]

        if date_from:
            result.append(f"**Period**: {date_from} to {date_to or 'present'}\n")

        purchase_data = safe_get(data, "data.data", [])

        if not purchase_data:
            result.append("No purchase data found for this period.")
            return "\n".join(result)

        # Calculate totals
        total_purchases = sum(safe_get(p, "total", 0) for p in purchase_data)
        result.append(f"**Total Purchases**: {format_currency(total_purchases)}\n")
        result.append(f"**Number of Vendors**: {len(purchase_data)}\n")

        # Top vendors
        result.append("\n## Top Vendors:\n")
        sorted_purchases = sorted(purchase_data, key=lambda x: safe_get(x, "total", 0), reverse=True)

        for idx, purchase in enumerate(sorted_purchases[:10], 1):
            vendor = safe_get(purchase, "contact_name", "Unknown")
            amount = safe_get(purchase, "total", 0)
            count = safe_get(purchase, "count", 0)
            result.append(f"{idx}. **{vendor}**: {format_currency(amount)} ({count} invoices)")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching purchase summary: {str(e)}"


async def _bank_balances(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get bank account balances."""
    try:
        data = await client.get(
            "bank",
            "balances",
            cache_category="realtime",
            force_refresh=True  # Always get fresh data for balances
        )

        result = ["# Bank Account Balances\n"]

        balances = safe_get(data, "data.data", [])

        if not balances:
            result.append("No bank accounts found.")
            return "\n".join(result)

        total_balance = 0

        for account in balances:
            name = safe_get(account, "name", "Unknown Account")
            balance = safe_get(account, "balance", 0)
            currency = safe_get(account, "currency", "IDR")

            total_balance += balance
            result.append(f"- **{name}**: {format_currency(balance, currency)}")

        result.append(f"\n**Total Balance**: {format_currency(total_balance)}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching bank balances: {str(e)}"
