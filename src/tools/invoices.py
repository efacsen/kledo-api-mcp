"""
Invoice tools for Kledo MCP Server
"""
from typing import Any, Dict
from mcp.types import Tool

from ..kledo_client import KledoAPIClient
from ..utils.helpers import parse_date_range, format_currency, safe_get


def get_tools() -> list[Tool]:
    """Get list of invoice tools."""
    return [
        Tool(
            name="invoice_list_sales",
            description="List sales invoices with optional filtering by customer, status, date range, or search term.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search term for invoice number or details"
                    },
                    "contact_id": {
                        "type": "integer",
                        "description": "Filter by customer ID"
                    },
                    "status_id": {
                        "type": "integer",
                        "description": "Filter by status (1=Draft, 2=Pending, 3=Paid, etc.)"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD or shortcuts like 'last_month')"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
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
            name="invoice_get_detail",
            description="Get detailed information about a specific invoice including line items.",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {
                        "type": "integer",
                        "description": "Invoice ID"
                    }
                },
                "required": ["invoice_id"]
            }
        ),
        Tool(
            name="invoice_get_totals",
            description="Get summary totals for sales invoices (total outstanding, paid, overdue, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Start date filter"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date filter"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="invoice_list_purchase",
            description="List purchase invoices (bills from vendors) with optional filtering.",
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
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 50)"
                    }
                },
                "required": []
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:
    """Handle invoice tool calls."""
    if name == "invoice_list_sales":
        return await _list_sales_invoices(arguments, client)
    elif name == "invoice_get_detail":
        return await _get_invoice_detail(arguments, client)
    elif name == "invoice_get_totals":
        return await _get_invoice_totals(arguments, client)
    elif name == "invoice_list_purchase":
        return await _list_purchase_invoices(arguments, client)
    else:
        return f"Unknown invoice tool: {name}"


async def _list_sales_invoices(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """List sales invoices."""
    # Parse date range
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        data = await client.list_invoices(
            search=args.get("search"),
            contact_id=args.get("contact_id"),
            status_id=args.get("status_id"),
            date_from=date_from,
            date_to=date_to,
            per_page=args.get("per_page", 50),
            force_refresh=args.get("force_refresh", False)
        )

        result = ["# Sales Invoices\n"]

        invoices = safe_get(data, "data.data", [])

        if not invoices:
            result.append("No invoices found matching the criteria.")
            return "\n".join(result)

        result.append(f"**Total Found**: {len(invoices)}\n")

        # Calculate summary
        total_amount = sum(safe_get(inv, "grand_total", 0) for inv in invoices)
        total_paid = sum(safe_get(inv, "amount_paid", 0) for inv in invoices)
        total_due = total_amount - total_paid

        result.append(f"**Total Amount**: {format_currency(total_amount)}")
        result.append(f"**Total Paid**: {format_currency(total_paid)}")
        result.append(f"**Total Outstanding**: {format_currency(total_due)}\n")

        result.append("\n## Invoices:\n")

        for invoice in invoices[:20]:  # Limit display
            inv_number = safe_get(invoice, "trans_number", "N/A")
            customer = safe_get(invoice, "contact_name", "Unknown")
            date = safe_get(invoice, "trans_date", "")
            amount = safe_get(invoice, "grand_total", 0)
            paid = safe_get(invoice, "amount_paid", 0)
            status = safe_get(invoice, "status_name", "Unknown")

            result.append(f"### {inv_number}")
            result.append(f"- **Customer**: {customer}")
            result.append(f"- **Date**: {date}")
            result.append(f"- **Amount**: {format_currency(amount)}")
            result.append(f"- **Paid**: {format_currency(paid)}")
            result.append(f"- **Status**: {status}\n")

        if len(invoices) > 20:
            result.append(f"... and {len(invoices) - 20} more invoices")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching sales invoices: {str(e)}"


async def _get_invoice_detail(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get invoice detail."""
    invoice_id = args.get("invoice_id")

    if not invoice_id:
        return "Error: invoice_id is required"

    try:
        data = await client.get_invoice_detail(invoice_id)

        invoice = safe_get(data, "data.data")
        if not invoice:
            return f"Invoice #{invoice_id} not found"

        result = ["# Invoice Details\n"]

        # Header info
        result.append(f"**Invoice Number**: {safe_get(invoice, 'trans_number', 'N/A')}")
        result.append(f"**Customer**: {safe_get(invoice, 'contact_name', 'Unknown')}")
        result.append(f"**Date**: {safe_get(invoice, 'trans_date', '')}")
        result.append(f"**Due Date**: {safe_get(invoice, 'due_date', '')}")
        result.append(f"**Status**: {safe_get(invoice, 'status_name', 'Unknown')}\n")

        # Amounts
        subtotal = safe_get(invoice, "subtotal", 0)
        tax = safe_get(invoice, "tax_amount", 0)
        total = safe_get(invoice, "grand_total", 0)
        paid = safe_get(invoice, "amount_paid", 0)
        due = total - paid

        result.append(f"**Subtotal**: {format_currency(subtotal)}")
        result.append(f"**Tax**: {format_currency(tax)}")
        result.append(f"**Total**: {format_currency(total)}")
        result.append(f"**Paid**: {format_currency(paid)}")
        result.append(f"**Due**: {format_currency(due)}\n")

        # Line items
        items = safe_get(invoice, "detail", [])
        if items:
            result.append("\n## Line Items:\n")
            for item in items:
                desc = safe_get(item, "desc", "Unknown item")
                qty = safe_get(item, "qty", 0)
                price = safe_get(item, "price", 0)
                amount = safe_get(item, "amount", 0)

                result.append(f"- **{desc}**")
                result.append(f"  - Qty: {qty} × {format_currency(price)} = {format_currency(amount)}")

        # Memo
        memo = safe_get(invoice, "memo")
        if memo:
            result.append(f"\n**Memo**: {memo}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching invoice details: {str(e)}"


async def _get_invoice_totals(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get invoice totals summary."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        data = await client.get(
            "invoices",
            "totals",
            params={
                "date_from": date_from,
                "date_to": date_to
            },
            cache_category="invoices"
        )

        result = ["# Invoice Totals Summary\n"]

        if date_from:
            result.append(f"**Period**: {date_from} to {date_to or 'present'}\n")

        totals = safe_get(data, "data.data", {})

        total_invoices = safe_get(totals, "total_count", 0)
        total_amount = safe_get(totals, "total_amount", 0)
        paid_amount = safe_get(totals, "paid_amount", 0)
        outstanding = safe_get(totals, "outstanding_amount", 0)
        overdue = safe_get(totals, "overdue_amount", 0)

        result.append(f"**Total Invoices**: {total_invoices}")
        result.append(f"**Total Amount**: {format_currency(total_amount)}")
        result.append(f"**Paid**: {format_currency(paid_amount)}")
        result.append(f"**Outstanding**: {format_currency(outstanding)}")
        result.append(f"**Overdue**: {format_currency(overdue)}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching invoice totals: {str(e)}"


async def _list_purchase_invoices(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """List purchase invoices."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        data = await client.get(
            "purchase_invoices",
            "list",
            params={
                "search": args.get("search"),
                "contact_id": args.get("contact_id"),
                "status_id": args.get("status_id"),
                "date_from": date_from,
                "date_to": date_to,
                "per_page": args.get("per_page", 50)
            },
            cache_category="invoices"
        )

        result = ["# Purchase Invoices\n"]

        invoices = safe_get(data, "data.data", [])

        if not invoices:
            result.append("No purchase invoices found.")
            return "\n".join(result)

        result.append(f"**Total Found**: {len(invoices)}\n")

        total_amount = sum(safe_get(inv, "grand_total", 0) for inv in invoices)
        result.append(f"**Total Amount**: {format_currency(total_amount)}\n")

        result.append("\n## Purchase Invoices:\n")

        for invoice in invoices[:20]:
            inv_number = safe_get(invoice, "trans_number", "N/A")
            vendor = safe_get(invoice, "contact_name", "Unknown")
            date = safe_get(invoice, "trans_date", "")
            amount = safe_get(invoice, "grand_total", 0)
            status = safe_get(invoice, "status_name", "Unknown")

            result.append(f"### {inv_number}")
            result.append(f"- **Vendor**: {vendor}")
            result.append(f"- **Date**: {date}")
            result.append(f"- **Amount**: {format_currency(amount)}")
            result.append(f"- **Status**: {status}\n")

        if len(invoices) > 20:
            result.append(f"... and {len(invoices) - 20} more invoices")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching purchase invoices: {str(e)}"
