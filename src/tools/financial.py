"""
Financial report tools for Kledo MCP Server
Fixed to use working endpoints (aggregate from /finance/invoices)
"""
from typing import Any, Dict
from mcp.types import Tool
from collections import defaultdict

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
            description="Get sales summary by customer for a period. Shows total sales revenue from each customer.",
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
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="financial_sales_by_person",
            description="Get sales summary by sales person for a period. Shows total sales per sales rep with invoice details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD or shortcuts like 'last_month', 'this_month')"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
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
    """Handle financial tool calls."""
    if name == "financial_activity_team_report":
        return await _activity_team_report(arguments, client)
    elif name == "financial_sales_summary":
        return await _sales_summary(arguments, client)
    elif name == "financial_sales_by_person":
        return await _sales_by_person(arguments, client)
    elif name == "financial_purchase_summary":
        return await _purchase_summary(arguments, client)
    elif name == "financial_bank_balances":
        return await _bank_balances(arguments, client)
    else:
        return f"Unknown financial tool: {name}"


async def _fetch_all_invoices(client: KledoAPIClient, date_from: str, date_to: str) -> list:
    """Fetch all invoices for a date range (handles pagination)."""
    all_invoices = []
    page = 1
    max_pages = 20  # Safety limit
    
    while page <= max_pages:
        data = await client.get(
            "invoices",
            "list",
            params={
                "date_from": date_from,
                "date_to": date_to,
                "per_page": 100,
                "page": page
            },
            cache_category="invoices"
        )
        
        invoices = safe_get(data, "data.data", [])
        if not invoices:
            break
            
        all_invoices.extend(invoices)
        
        current_page = safe_get(data, "data.current_page", 1)
        last_page = safe_get(data, "data.last_page", 1)
        
        if current_page >= last_page:
            break
        page += 1
    
    return all_invoices


async def _activity_team_report(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get team activity report."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    # Convert to YYYY-MM format if full date provided
    if date_from and len(date_from) == 10:
        date_from = date_from[:7]
    if date_to and len(date_to) == 10:
        date_to = date_to[:7]

    try:
        data = await client.get_activity_team_report(date_from, date_to)

        result = ["# Team Activity Report\n"]

        if date_from:
            result.append(f"**Period**: {date_from} to {date_to or 'present'}\n")

        report_data = safe_get(data, "data.data", [])

        if not report_data:
            result.append("No activity data found for this period.")
            return "\n".join(result)

        result.append(f"\n**Total Activities**: {len(report_data)}\n")

        for activity in report_data[:20]:
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
    """Get sales summary by customer - aggregated from invoices."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        # Fetch all invoices and aggregate by customer
        invoices = await _fetch_all_invoices(client, date_from, date_to)

        result = ["# Sales Summary by Customer\n"]

        if date_from:
            result.append(f"**Period**: {date_from} to {date_to or 'present'}\n")

        if not invoices:
            result.append("No invoice data found for this period.")
            return "\n".join(result)

        # Aggregate by customer
        customer_sales = defaultdict(lambda: {"total": 0, "paid": 0, "count": 0})
        
        for inv in invoices:
            customer_name = safe_get(inv, "contact.name", "Unknown")
            amount = safe_get(inv, "amount_after_tax", 0)
            status_id = safe_get(inv, "status_id", 1)
            
            customer_sales[customer_name]["total"] += amount
            customer_sales[customer_name]["count"] += 1
            if status_id == 3:  # Paid
                customer_sales[customer_name]["paid"] += amount

        # Calculate totals
        total_sales = sum(c["total"] for c in customer_sales.values())
        total_paid = sum(c["paid"] for c in customer_sales.values())
        
        result.append(f"**Total Revenue**: {format_currency(total_sales)}")
        result.append(f"**Total Paid**: {format_currency(total_paid)}")
        result.append(f"**Outstanding**: {format_currency(total_sales - total_paid)}")
        result.append(f"**Number of Customers**: {len(customer_sales)}")
        result.append(f"**Total Invoices**: {len(invoices)}\n")

        # Top customers by revenue
        result.append("\n## Top Customers:\n")
        sorted_customers = sorted(customer_sales.items(), key=lambda x: x[1]["total"], reverse=True)

        for idx, (customer, data) in enumerate(sorted_customers[:10], 1):
            status = "✅" if data["paid"] == data["total"] else "🔴"
            result.append(f"{idx}. **{customer}**: {format_currency(data['total'])} ({data['count']} inv) {status}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching sales summary: {str(e)}"


async def _sales_by_person(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get sales summary by sales person - aggregated from invoices."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        invoices = await _fetch_all_invoices(client, date_from, date_to)

        result = ["# Sales by Sales Person\n"]

        if date_from:
            result.append(f"**Period**: {date_from} to {date_to or 'present'}\n")

        if not invoices:
            result.append("No invoice data found for this period.")
            return "\n".join(result)

        # Aggregate by sales person
        sales_person_data = defaultdict(lambda: {
            "total": 0, 
            "paid": 0, 
            "count": 0,
            "invoices": []
        })
        
        for inv in invoices:
            # Get sales person name - use None check properly
            sales_person = inv.get("sales_person")
            if sales_person and isinstance(sales_person, dict):
                sp_name = sales_person.get("name", "(Tidak Ada Sales)")
            else:
                sp_name = "(Tidak Ada Sales)"
            
            amount = safe_get(inv, "amount_after_tax", 0)
            status_id = safe_get(inv, "status_id", 1)
            
            sales_person_data[sp_name]["total"] += amount
            sales_person_data[sp_name]["count"] += 1
            if status_id == 3:
                sales_person_data[sp_name]["paid"] += amount
            
            # Store invoice details (limit to prevent too much data)
            if len(sales_person_data[sp_name]["invoices"]) < 10:
                sales_person_data[sp_name]["invoices"].append({
                    "ref": safe_get(inv, "ref_number", ""),
                    "customer": safe_get(inv, "contact.name", ""),
                    "amount": amount,
                    "status": "Lunas" if status_id == 3 else "Unpaid"
                })

        # Calculate totals
        total_sales = sum(s["total"] for s in sales_person_data.values())
        
        result.append(f"**Total Revenue**: {format_currency(total_sales)}")
        result.append(f"**Total Invoices**: {len(invoices)}\n")

        # Sort by total descending
        sorted_sales = sorted(sales_person_data.items(), key=lambda x: x[1]["total"], reverse=True)

        result.append("## Performance Summary:\n")
        result.append("| Sales Person | Invoices | Total | Paid | Outstanding |")
        result.append("|--------------|----------|-------|------|-------------|")

        for sp_name, data in sorted_sales:
            outstanding = data["total"] - data["paid"]
            result.append(f"| {sp_name} | {data['count']} | {format_currency(data['total'])} | {format_currency(data['paid'])} | {format_currency(outstanding)} |")

        # Detail per person
        result.append("\n## Invoice Details:\n")
        for sp_name, data in sorted_sales:
            if sp_name == "(Tidak Ada Sales)":
                continue
            result.append(f"\n### {sp_name}")
            for inv in data["invoices"]:
                status_emoji = "✅" if inv["status"] == "Lunas" else "🔴"
                result.append(f"- {inv['ref']} | {inv['customer']} | {format_currency(inv['amount'])} {status_emoji}")
            if data["count"] > len(data["invoices"]):
                result.append(f"- ... dan {data['count'] - len(data['invoices'])} invoice lainnya")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching sales by person: {str(e)}"


async def _purchase_summary(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get purchase summary by vendor - aggregated from purchase invoices."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        # Fetch purchase invoices
        all_purchases = []
        page = 1
        max_pages = 20
        
        while page <= max_pages:
            data = await client.get(
                "purchase_invoices",
                "list",
                params={
                    "date_from": date_from,
                    "date_to": date_to,
                    "per_page": 100,
                    "page": page
                },
                cache_category="purchases"
            )
            
            purchases = safe_get(data, "data.data", [])
            if not purchases:
                break
                
            all_purchases.extend(purchases)
            
            current_page = safe_get(data, "data.current_page", 1)
            last_page = safe_get(data, "data.last_page", 1)
            
            if current_page >= last_page:
                break
            page += 1

        result = ["# Purchase Summary by Vendor\n"]

        if date_from:
            result.append(f"**Period**: {date_from} to {date_to or 'present'}\n")

        if not all_purchases:
            result.append("No purchase data found for this period.")
            return "\n".join(result)

        # Aggregate by vendor
        vendor_purchases = defaultdict(lambda: {"total": 0, "paid": 0, "count": 0})
        
        for pi in all_purchases:
            vendor_name = safe_get(pi, "contact.name", "Unknown")
            amount = safe_get(pi, "amount_after_tax", 0) or safe_get(pi, "gross_amount", 0)
            status_id = safe_get(pi, "status_id", 1)
            
            vendor_purchases[vendor_name]["total"] += amount
            vendor_purchases[vendor_name]["count"] += 1
            if status_id == 3:
                vendor_purchases[vendor_name]["paid"] += amount

        total_purchases = sum(v["total"] for v in vendor_purchases.values())
        total_paid = sum(v["paid"] for v in vendor_purchases.values())
        
        result.append(f"**Total Purchases**: {format_currency(total_purchases)}")
        result.append(f"**Total Paid**: {format_currency(total_paid)}")
        result.append(f"**Outstanding**: {format_currency(total_purchases - total_paid)}")
        result.append(f"**Number of Vendors**: {len(vendor_purchases)}\n")

        # Top vendors
        result.append("\n## Top Vendors:\n")
        sorted_vendors = sorted(vendor_purchases.items(), key=lambda x: x[1]["total"], reverse=True)

        for idx, (vendor, data) in enumerate(sorted_vendors[:10], 1):
            status = "✅" if data["paid"] == data["total"] else "🔴"
            result.append(f"{idx}. **{vendor}**: {format_currency(data['total'])} ({data['count']} inv) {status}")

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
            force_refresh=True
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
