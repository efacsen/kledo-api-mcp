"""
Sales Analytics Tools
Tools for sales representative revenue analysis and reporting
"""
from typing import Any
from datetime import datetime
from collections import defaultdict
from decimal import Decimal
from mcp.types import Tool

from ..kledo_client import KledoAPIClient
from ..utils.helpers import format_markdown_table, parse_natural_date


def get_tools() -> list[Tool]:
    """Get list of sales analytics tools."""
    return [
        Tool(
            name="sales_rep_revenue_report",
            description="""Calculate sales representative revenue for commission and performance analysis.

**IMPORTANT:** Only counts PAID invoices (status_id=3 / Lunas) for accurate commission calculation.

Shows both:
- Revenue BEFORE tax (subtotal) - USE FOR COMMISSION CALCULATION
- Revenue AFTER tax (amount_after_tax) - Actual revenue with tax

Includes:
- Total revenue per sales representative (before/after tax)
- Monthly/daily breakdown of sales
- Customer count per sales rep
- Average deal size
- Top largest deals

**Use this for:**
- Sales commission calculation (uses PAID invoices only, before tax)
- Performance analysis
- Monthly/weekly revenue reports
- Sales rep comparisons

**Returns:** Detailed revenue report with both before-tax (commission) and after-tax (actual) amounts.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD or natural language like 'last month', '2026-01-01')"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD or natural language like 'today', '2026-01-31')"
                    },
                    "sales_rep_id": {
                        "type": "integer",
                        "description": "Optional: Filter by specific sales rep ID (use sales_rep_list to find IDs)"
                    },
                    "group_by": {
                        "type": "string",
                        "description": "How to group results: 'month' (default) or 'day'",
                        "enum": ["month", "day"]
                    }
                },
                "required": ["start_date", "end_date"]
            }
        ),
        Tool(
            name="sales_rep_list",
            description="""List all sales representatives who have created invoices with their performance metrics.

Shows:
- Sales rep ID and name
- Number of invoices created
- Total revenue generated

Use this to find sales_rep_id for filtering in sales_rep_revenue_report.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


async def handle_tool(name: str, arguments: dict[str, Any], client: KledoAPIClient) -> str:
    """Handle sales analytics tool calls."""

    if name == "sales_rep_revenue_report":
        return await _sales_rep_revenue_report(client, arguments)
    elif name == "sales_rep_list":
        return await _sales_rep_list(client)
    else:
        return f"Unknown tool: {name}"


async def _sales_rep_revenue_report(client: KledoAPIClient, args: dict[str, Any]) -> str:
    """Calculate sales rep revenue for a time period."""

    start_date = args.get("start_date", "")
    end_date = args.get("end_date", "")
    sales_rep_id = args.get("sales_rep_id")
    group_by = args.get("group_by", "month")

    # Parse dates
    start = parse_natural_date(start_date)
    end = parse_natural_date(end_date)

    if not start or not end:
        return f"❌ Error: Could not parse dates. Start: {start_date}, End: {end_date}"

    # Fetch all invoices in the date range
    all_invoices = []
    page = 1
    per_page = 100

    while True:
        response = await client.get(
            category="invoices",
            name="list",
            params={
                "per_page": per_page,
                "page": page,
                "date_from": start.strftime("%Y-%m-%d"),
                "date_to": end.strftime("%Y-%m-%d"),
                "status_ids": "3"  # Only paid invoices (status_id=3)
            }
        )

        if not response or "data" not in response:
            break

        # Handle pagination wrapper
        data = response["data"]
        if isinstance(data, dict) and "data" in data:
            items = data["data"]
            if not items:
                break
            all_invoices.extend(items)

            # Check if there are more pages
            if data.get("current_page", 1) >= data.get("last_page", 1):
                break
            page += 1
        else:
            break

    if not all_invoices:
        return f"No paid invoices found between {start.strftime('%Y-%m-%d')} and {end.strftime('%Y-%m-%d')}"

    # Analyze invoices - track BOTH before and after tax
    sales_rep_data = defaultdict(lambda: {
        "revenue_before_tax": Decimal(0),  # For commission calculation
        "revenue_after_tax": Decimal(0),   # Actual revenue with tax
        "total_tax": Decimal(0),
        "invoice_count": 0,
        "customer_ids": set(),
        "invoices": [],
        "monthly_revenue_before_tax": defaultdict(Decimal),
        "monthly_revenue_after_tax": defaultdict(Decimal)
    })

    for invoice in all_invoices:
        # Get sales person info
        sales_person = invoice.get("sales_person") or {}
        rep_id = sales_person.get("id")
        rep_name = sales_person.get("name", "Unknown")

        # Skip if filtering by sales rep
        if sales_rep_id and rep_id != sales_rep_id:
            continue

        # Parse amounts - BOTH before and after tax
        subtotal = Decimal(str(invoice.get("subtotal", 0)))  # Before tax (commission)
        tax_amount = Decimal(str(invoice.get("total_tax", 0)))
        amount_after_tax = Decimal(str(invoice.get("amount_after_tax", 0)))  # With tax (actual)
        trans_date = invoice.get("trans_date", "")

        # Group by month or day
        if trans_date:
            date_obj = datetime.strptime(trans_date, "%Y-%m-%d")
            if group_by == "month":
                period_key = date_obj.strftime("%Y-%m")
            else:
                period_key = trans_date
        else:
            period_key = "Unknown"

        # Aggregate data
        rep_key = f"{rep_id}:{rep_name}"
        sales_rep_data[rep_key]["revenue_before_tax"] += subtotal
        sales_rep_data[rep_key]["revenue_after_tax"] += amount_after_tax
        sales_rep_data[rep_key]["total_tax"] += tax_amount
        sales_rep_data[rep_key]["invoice_count"] += 1
        sales_rep_data[rep_key]["monthly_revenue_before_tax"][period_key] += subtotal
        sales_rep_data[rep_key]["monthly_revenue_after_tax"][period_key] += amount_after_tax

        # Track unique customers
        contact = invoice.get("contact") or {}
        if contact.get("id"):
            sales_rep_data[rep_key]["customer_ids"].add(contact["id"])

        # Store invoice reference
        sales_rep_data[rep_key]["invoices"].append({
            "ref": invoice.get("ref_number"),
            "date": trans_date,
            "amount_before_tax": float(subtotal),
            "amount_after_tax": float(amount_after_tax),
            "customer": contact.get("name", "Unknown")
        })

    # Build report
    report_lines = []
    report_lines.append(f"# Sales Representative Revenue Report (PAID INVOICES ONLY)")
    report_lines.append(f"")
    report_lines.append(f"**Period:** {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    report_lines.append(f"**Total Paid Invoices:** {len(all_invoices)} (status_id=3 / Lunas)")
    report_lines.append(f"**Group By:** {group_by}")
    report_lines.append(f"")
    report_lines.append(f"**Note:** Revenue Before Tax is used for commission calculation")
    report_lines.append(f"")

    # Summary table
    summary_data = []
    for rep_key, data in sorted(
        sales_rep_data.items(),
        key=lambda x: x[1]["revenue_before_tax"],  # Sort by commission amount
        reverse=True
    ):
        rep_name = rep_key.split(":", 1)[1]
        avg_deal_before_tax = data["revenue_before_tax"] / data["invoice_count"] if data["invoice_count"] > 0 else Decimal(0)

        summary_data.append([
            rep_name,
            f"Rp {data['revenue_before_tax']:,.0f}",  # Commission base
            f"Rp {data['revenue_after_tax']:,.0f}",   # Actual revenue
            str(data["invoice_count"]),
            str(len(data["customer_ids"])),
            f"Rp {avg_deal_before_tax:,.0f}"
        ])

    report_lines.append("## Summary by Sales Representative")
    report_lines.append("")
    report_lines.append(format_markdown_table(
        headers=["Sales Rep", "Revenue Before Tax (Commission)", "Revenue After Tax (Actual)", "Invoices", "Customers", "Avg Deal"],
        rows=summary_data
    ))
    report_lines.append("")

    # Monthly/daily breakdown for each rep
    report_lines.append(f"## Breakdown by {group_by.title()}")
    report_lines.append("")

    for rep_key, data in sorted(
        sales_rep_data.items(),
        key=lambda x: x[1]["revenue_before_tax"],
        reverse=True
    ):
        rep_name = rep_key.split(":", 1)[1]
        report_lines.append(f"### {rep_name}")
        report_lines.append("")

        period_data = []
        for period in sorted(data["monthly_revenue_before_tax"].keys()):
            before_tax = data["monthly_revenue_before_tax"][period]
            after_tax = data["monthly_revenue_after_tax"][period]
            period_data.append([
                period,
                f"Rp {before_tax:,.0f}",
                f"Rp {after_tax:,.0f}"
            ])

        if period_data:
            report_lines.append(format_markdown_table(
                headers=["Period", "Before Tax (Commission)", "After Tax (Actual)"],
                rows=period_data
            ))
            report_lines.append("")

    # Top 10 largest deals (sorted by before-tax amount for commission)
    all_invoices_sorted = []
    for rep_key, data in sales_rep_data.items():
        rep_name = rep_key.split(":", 1)[1]
        for inv in data["invoices"]:
            all_invoices_sorted.append({
                **inv,
                "sales_rep": rep_name
            })

    all_invoices_sorted.sort(key=lambda x: x["amount_before_tax"], reverse=True)

    if all_invoices_sorted:
        report_lines.append("## Top 10 Largest Deals (by Commission Amount)")
        report_lines.append("")

        top_deals = []
        for inv in all_invoices_sorted[:10]:
            top_deals.append([
                inv["ref"],
                inv["date"],
                inv["sales_rep"],
                inv["customer"],
                f"Rp {inv['amount_before_tax']:,.0f}",
                f"Rp {inv['amount_after_tax']:,.0f}"
            ])

        report_lines.append(format_markdown_table(
            headers=["Invoice #", "Date", "Sales Rep", "Customer", "Before Tax", "After Tax"],
            rows=top_deals
        ))

    return "\n".join(report_lines)


async def _sales_rep_list(client: KledoAPIClient) -> str:
    """List all sales representatives."""

    # Fetch recent PAID invoices to find sales reps (status_id=3)
    response = await client.get(
        category="invoices",
        name="list",
        params={"per_page": 100, "page": 1, "status_ids": "3"}
    )

    if not response or "data" not in response:
        return "No invoices found"

    data = response["data"]
    if isinstance(data, dict) and "data" in data:
        items = data["data"]
    else:
        items = []

    # Collect unique sales reps with both revenue amounts
    sales_reps = {}
    for invoice in items:
        sales_person = invoice.get("sales_person") or {}
        rep_id = sales_person.get("id")
        rep_name = sales_person.get("name", "Unknown")

        if rep_id:
            if rep_id not in sales_reps:
                sales_reps[rep_id] = {
                    "name": rep_name,
                    "invoice_count": 0,
                    "revenue_before_tax": Decimal(0),
                    "revenue_after_tax": Decimal(0)
                }

            sales_reps[rep_id]["invoice_count"] += 1
            subtotal = Decimal(str(invoice.get("subtotal", 0)))
            amount_after_tax = Decimal(str(invoice.get("amount_after_tax", 0)))
            sales_reps[rep_id]["revenue_before_tax"] += subtotal
            sales_reps[rep_id]["revenue_after_tax"] += amount_after_tax

    # Build table
    rows = []
    for rep_id, data in sorted(sales_reps.items()):
        rows.append([
            str(rep_id),
            data["name"],
            str(data["invoice_count"]),
            f"Rp {data['revenue_before_tax']:,.0f}",
            f"Rp {data['revenue_after_tax']:,.0f}"
        ])

    table = format_markdown_table(
        headers=["ID", "Name", "Paid Invoices", "Revenue (Before Tax)", "Revenue (After Tax)"],
        rows=rows
    )

    return f"# Sales Representatives\n\n{table}\n\n_Based on last 100 PAID invoices (status_id=3)_\n_Before Tax = Commission Base | After Tax = Actual Revenue_"
