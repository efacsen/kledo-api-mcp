"""
Revenue and Receivables Tools for Kledo MCP Server
Quick revenue summaries and outstanding payment tracking
"""
from typing import Any, Dict
from mcp.types import Tool
from decimal import Decimal
from collections import defaultdict

from ..kledo_client import KledoAPIClient
from ..utils.helpers import parse_date_range, format_currency, safe_get, format_markdown_table
from ..mappers.kledo_mapper import from_kledo_invoices, aggregate_financials


def get_tools() -> list[Tool]:
    """Get list of revenue tools."""
    return [
        Tool(
            name="revenue_summary",
            description="""Get quick revenue summary for a time period.

Shows financial overview:
- Net Sales (Penjualan Neto) - revenue before tax
- PPN Collected - tax collected
- Gross Sales (Penjualan Bruto) - total including tax

**IMPORTANT:** Only counts PAID invoices (status_id=3 / Lunas)

Perfect for answering:
- "Berapa revenue bulan ini?"
- "What's this month's revenue?"
- "Revenue January 2026?"

Returns Net Sales and Gross Sales with Indonesian business terminology.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD or 'this_month', 'last_month', 'this_year')"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD). Optional if using shortcuts."
                    }
                },
                "required": ["date_from"]
            }
        ),
        Tool(
            name="outstanding_receivables",
            description="""Get list of unpaid and partially paid invoices (piutang).

Shows all invoices with outstanding payments:
- Status 1 (Belum Dibayar / Unpaid)
- Status 2 (Dibayar Sebagian / Partially Paid)

Groups by status and shows:
- Customer names
- Invoice numbers
- Outstanding amounts
- Days overdue

Perfect for answering:
- "Siapa yang belum bayar?"
- "Invoice yang belum dibayar"
- "Total piutang"
- "Outstanding receivables"

Sorted by amount due (largest first).""",
            inputSchema={
                "type": "object",
                "properties": {
                    "status_id": {
                        "type": "integer",
                        "description": "Filter by status: 1=Unpaid, 2=Partially Paid. Leave empty for both."
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "Show only invoices with due amount >= this value"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="customer_revenue_ranking",
            description="""Get top customers by revenue for a time period.

Shows customer ranking with:
- Net Sales (Penjualan Neto) and Gross Sales (Penjualan Bruto)
- Number of invoices
- Average invoice value
- Company name (if available)

**IMPORTANT:** Only counts PAID invoices (status_id=3 / Lunas)

Perfect for answering:
- "Siapa customer terbesar bulan ini?"
- "Who are our top customers?"
- "Customer dengan revenue tertinggi"

Sorted by Net Sales (highest first).""",
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
                    "limit": {
                        "type": "integer",
                        "description": "Number of top customers to show (default: 10)"
                    }
                },
                "required": ["date_from"]
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:
    """Handle revenue tool calls."""
    if name == "revenue_summary":
        return await _revenue_summary(arguments, client)
    elif name == "outstanding_receivables":
        return await _outstanding_receivables(arguments, client)
    elif name == "customer_revenue_ranking":
        return await _customer_revenue_ranking(arguments, client)
    else:
        return f"Unknown revenue tool: {name}"


async def _revenue_summary(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get revenue summary for a period."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    # Parse date range
    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        # Fetch PAID invoices only (status_id=3)
        data = await client.list_invoices(
            status_id=3,  # LUNAS / Paid
            date_from=date_from,
            date_to=date_to,
            per_page=100
        )

        invoices = safe_get(data, "data.data", [])

        if not invoices:
            return f"No paid invoices found for period: {date_from} to {date_to}"

        # Convert to domain model and aggregate
        financial_data = from_kledo_invoices(invoices, skip_invalid=True, include_metadata=False)
        summary = aggregate_financials(financial_data)

        # Use clear business terminology
        total_net_sales = summary.net_sales
        total_tax_collected = summary.tax_collected
        total_gross_sales = summary.gross_sales

        result = ["# Revenue Summary (PAID INVOICES ONLY)\n"]
        result.append(f"**Period**: {date_from} to {date_to}")
        result.append(f"**Paid Invoices**: {len(invoices)}\n")

        result.append("## Financial Overview:")
        result.append(f"**Penjualan Neto (Net Sales)**: {format_currency(float(total_net_sales))}")
        result.append(f"**PPN Collected**: {format_currency(float(total_tax_collected))}")
        result.append(f"**Penjualan Bruto (Gross Sales)**: {format_currency(float(total_gross_sales))}\n")

        # Calculate average invoice
        invoice_count = len(financial_data) if financial_data else 1
        avg_net_sales = total_net_sales / invoice_count
        avg_gross_sales = total_gross_sales / invoice_count

        result.append("## Statistics:")
        result.append(f"**Average Invoice (Net Sales)**: {format_currency(float(avg_net_sales))}")
        result.append(f"**Average Invoice (Gross Sales)**: {format_currency(float(avg_gross_sales))}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching revenue summary: {str(e)}"


async def _outstanding_receivables(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get outstanding receivables (unpaid/partially paid invoices)."""
    status_filter = args.get("status_id")
    min_amount = args.get("min_amount", 0)

    try:
        # Fetch invoices with outstanding payments
        all_invoices = []

        # If no status filter, get both unpaid (1) and partial (2)
        if status_filter:
            statuses = [status_filter]
        else:
            statuses = [1, 2]  # Unpaid and Partially Paid

        for status_id in statuses:
            data = await client.list_invoices(
                status_id=status_id,
                per_page=100
            )
            invoices = safe_get(data, "data.data", [])
            all_invoices.extend(invoices)

        # Filter by minimum amount and sort
        outstanding = [
            inv for inv in all_invoices
            if float(safe_get(inv, "due", 0)) >= min_amount
        ]
        outstanding.sort(key=lambda x: float(safe_get(x, "due", 0)), reverse=True)

        if not outstanding:
            return "No outstanding receivables found."

        # Calculate totals
        total_due = sum(float(safe_get(inv, "due", 0)) for inv in outstanding)

        # Group by status
        by_status = defaultdict(list)
        for inv in outstanding:
            by_status[safe_get(inv, "status_id", 0)].append(inv)

        result = ["# Outstanding Receivables (Piutang)\n"]
        result.append(f"**Total Outstanding**: {format_currency(total_due)}")
        result.append(f"**Total Invoices**: {len(outstanding)}\n")

        # Status 1: Belum Dibayar (Unpaid)
        if 1 in by_status:
            unpaid = by_status[1]
            unpaid_total = sum(float(safe_get(inv, "due", 0)) for inv in unpaid)

            result.append(f"## Belum Dibayar (Unpaid): {len(unpaid)} invoices")
            result.append(f"**Total**: {format_currency(unpaid_total)}\n")

            rows = []
            for inv in unpaid[:10]:
                customer = safe_get(inv, "contact.name", "Unknown")
                inv_number = safe_get(inv, "ref_number", "N/A")
                date = safe_get(inv, "trans_date", "")
                due = float(safe_get(inv, "due", 0))

                rows.append([inv_number, customer, date, format_currency(due)])

            result.append(format_markdown_table(
                headers=["Invoice #", "Customer", "Date", "Outstanding"],
                rows=rows
            ))
            result.append("")

        # Status 2: Dibayar Sebagian (Partially Paid)
        if 2 in by_status:
            partial = by_status[2]
            partial_total = sum(float(safe_get(inv, "due", 0)) for inv in partial)

            result.append(f"## Dibayar Sebagian (Partially Paid): {len(partial)} invoices")
            result.append(f"**Total**: {format_currency(partial_total)}\n")

            rows = []
            for inv in partial[:10]:
                customer = safe_get(inv, "contact.name", "Unknown")
                inv_number = safe_get(inv, "ref_number", "N/A")
                date = safe_get(inv, "trans_date", "")
                amount_total = float(safe_get(inv, "amount_after_tax", 0))
                due = float(safe_get(inv, "due", 0))
                paid = amount_total - due
                paid_pct = (paid / amount_total * 100) if amount_total > 0 else 0

                rows.append([
                    inv_number,
                    customer,
                    date,
                    f"{paid_pct:.0f}%",
                    format_currency(due)
                ])

            result.append(format_markdown_table(
                headers=["Invoice #", "Customer", "Date", "Paid %", "Outstanding"],
                rows=rows
            ))
            result.append("")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching outstanding receivables: {str(e)}"


async def _customer_revenue_ranking(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get top customers by revenue."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")
    limit = args.get("limit", 10)

    # Parse date range
    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        # Fetch PAID invoices only
        data = await client.list_invoices(
            status_id=3,  # LUNAS / Paid
            date_from=date_from,
            date_to=date_to,
            per_page=100
        )

        invoices = safe_get(data, "data.data", [])

        if not invoices:
            return f"No paid invoices found for period: {date_from} to {date_to}"

        # Group by customer using domain terminology
        customer_data = defaultdict(lambda: {
            "name": "",
            "company": "",
            "net_sales": Decimal(0),
            "gross_sales": Decimal(0),
            "invoice_count": 0
        })

        for inv in invoices:
            contact = safe_get(inv, "contact") or {}
            contact_id = contact.get("id")

            if contact_id:
                customer_data[contact_id]["name"] = contact.get("name", "Unknown")
                customer_data[contact_id]["company"] = contact.get("company", "")
                customer_data[contact_id]["net_sales"] += Decimal(str(safe_get(inv, "subtotal", 0)))
                customer_data[contact_id]["gross_sales"] += Decimal(str(safe_get(inv, "amount_after_tax", 0)))
                customer_data[contact_id]["invoice_count"] += 1

        # Sort by net sales (highest first)
        sorted_customers = sorted(
            customer_data.items(),
            key=lambda x: x[1]["net_sales"],
            reverse=True
        )[:limit]

        result = ["# Top Customers by Revenue (PAID INVOICES ONLY)\n"]
        result.append(f"**Period**: {date_from} to {date_to}")
        result.append(f"**Total Customers**: {len(customer_data)}\n")

        # Build table with clear terminology
        rows = []
        for i, (customer_id, cust_data) in enumerate(sorted_customers, 1):
            name = cust_data["name"]
            if cust_data["company"]:
                name = f"{name} ({cust_data['company']})"

            avg_net_sales = cust_data["net_sales"] / cust_data["invoice_count"] if cust_data["invoice_count"] > 0 else Decimal(0)

            rows.append([
                str(i),
                name,
                str(cust_data["invoice_count"]),
                f"Rp {cust_data['net_sales']:,.0f}",
                f"Rp {cust_data['gross_sales']:,.0f}",
                f"Rp {avg_net_sales:,.0f}"
            ])

        result.append(format_markdown_table(
            headers=["Rank", "Customer", "Invoices", "Net Sales", "Gross Sales", "Avg Invoice"],
            rows=rows
        ))

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching customer ranking: {str(e)}"
