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
from ..utils.helpers import format_markdown_table, format_currency, parse_natural_date
from ..mappers.kledo_mapper import from_kledo_invoice


def get_tools() -> list[Tool]:
    """Get list of sales analytics tools."""
    return [
        Tool(
            name="sales_rep_revenue_report",
            description="""Calculate sales representative revenue and performance analysis.

**IMPORTANT:** Only counts PAID invoices (status_id=3 / Lunas).

Shows:
- Net Sales (Penjualan Neto) - revenue before tax
- Gross Sales (Penjualan Bruto) - total including tax
- PPN Collected - tax collected

**IMPORTANT UPDATE:** You can now filter by sales rep using EITHER:
- `sales_rep_id` - Direct sales rep ID (number)
- `sales_rep_name` - Sales rep name (string) - system will auto-find the ID

When using `sales_rep_name`, the system will:
1. Fetch invoices from the date range
2. Search for sales reps with matching names
3. Use the found ID to filter results

**Use this for:**
- Performance analysis
- Monthly/weekly revenue reports
- Sales rep comparisons

**Returns:** Detailed revenue report with Net Sales and Gross Sales.""",
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
                        "description": "Filter by specific sales rep ID (optional)"
                    },
                    "sales_rep_name": {
                        "type": "string",
                        "description": "Filter by sales rep name (optional). System will auto-find the ID. Supports partial match and case-insensitive."
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
- Total revenue generated (Net Sales and Gross Sales)

**IMPORTANT:** Only counts PAID invoices (status_id=3 / Lunas)

Optional: Filter by date range to see performance for specific period.
If no dates provided, shows last 100 paid invoices.

Use this to find sales_rep_id for filtering in sales_rep_revenue_report.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD). Optional - if not provided, shows last 100 invoices"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD). Optional - required if date_from is provided"
                    }
                },
                "required": []
            }
        )
    ]


async def handle_tool(name: str, arguments: dict[str, Any], client: KledoAPIClient) -> str:
    """Handle sales analytics tool calls."""

    if name == "sales_rep_revenue_report":
        return await _sales_rep_revenue_report(client, arguments)
    elif name == "sales_rep_list":
        return await _sales_rep_list(client, arguments)
    else:
        return f"Unknown tool: {name}"


async def _sales_rep_revenue_report(client: KledoAPIClient, args: dict[str, Any]) -> str:
    """Calculate sales rep revenue for a time period."""

    start_date = args.get("start_date", "")
    end_date = args.get("end_date", "")
    sales_rep_id = args.get("sales_rep_id")
    sales_rep_name = args.get("sales_rep_name")
    group_by = args.get("group_by", "month")

    # Parse dates
    start = parse_natural_date(start_date)
    end = parse_natural_date(end_date)

    if not start or not end:
        return f"❌ Error: Could not parse dates. Start: {start_date}, End: {end_date}"

    # If sales_rep_name is provided, find the sales rep ID first
    if sales_rep_name and not sales_rep_id:
        # Fetch invoices to find sales reps with matching names
        sales_rep_id = await _find_sales_rep_id_by_name(client, start, end, sales_rep_name)
        if sales_rep_id is None:
            return f"❌ Error: Could not find sales rep with name '{sales_rep_name}' in the date range. Please check the name or use 'sales_rep_list' to see available reps."

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

    # Analyze invoices using domain model terminology
    sales_rep_data = defaultdict(lambda: {
        "net_sales": Decimal(0),
        "gross_sales": Decimal(0),
        "tax_collected": Decimal(0),
        "invoice_count": 0,
        "customer_ids": set(),
        "invoices": [],
        "monthly_net_sales": defaultdict(Decimal),
        "monthly_gross_sales": defaultdict(Decimal)
    })

    for invoice in all_invoices:
        # Get sales person info
        sales_person = invoice.get("sales_person") or {}
        rep_id = sales_person.get("id")
        rep_name = sales_person.get("name", "Unknown")

        # Skip if filtering by sales rep
        if sales_rep_id and rep_id != sales_rep_id:
            continue

        # Convert to domain model (skip conversion failures)
        try:
            financials = from_kledo_invoice(invoice, include_metadata=False)
        except (ValueError, KeyError):
            continue  # Skip invalid invoices

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

        # Aggregate data using domain model
        rep_key = f"{rep_id}:{rep_name}"
        sales_rep_data[rep_key]["net_sales"] += financials.net_sales
        sales_rep_data[rep_key]["gross_sales"] += financials.gross_sales
        sales_rep_data[rep_key]["tax_collected"] += financials.tax_collected
        sales_rep_data[rep_key]["invoice_count"] += 1
        sales_rep_data[rep_key]["monthly_net_sales"][period_key] += financials.net_sales
        sales_rep_data[rep_key]["monthly_gross_sales"][period_key] += financials.gross_sales

        # Track unique customers
        contact = invoice.get("contact") or {}
        if contact.get("id"):
            sales_rep_data[rep_key]["customer_ids"].add(contact["id"])

        # Store invoice reference
        sales_rep_data[rep_key]["invoices"].append({
            "ref": invoice.get("ref_number"),
            "date": trans_date,
            "net_sales": float(financials.net_sales),
            "gross_sales": float(financials.gross_sales),
            "customer": contact.get("name", "Unknown")
        })

    # Build report
    report_lines = []
    report_lines.append("# Sales Representative Revenue Report (PAID INVOICES ONLY)")
    report_lines.append("")
    report_lines.append(f"**Period:** {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    report_lines.append(f"**Total Paid Invoices:** {len(all_invoices)} (status_id=3 / Lunas)")
    report_lines.append(f"**Group By:** {group_by}")
    report_lines.append("")

    # Summary table with domain terminology
    summary_data = []
    for rep_key, rep_data in sorted(
        sales_rep_data.items(),
        key=lambda x: x[1]["net_sales"],
        reverse=True
    ):
        rep_name = rep_key.split(":", 1)[1]
        avg_deal_net = rep_data["net_sales"] / rep_data["invoice_count"] if rep_data["invoice_count"] > 0 else Decimal(0)

        summary_data.append([
            rep_name,
            format_currency(float(rep_data['net_sales']), short=True),
            format_currency(float(rep_data['gross_sales']), short=True),
            str(rep_data["invoice_count"]),
            str(len(rep_data["customer_ids"])),
            format_currency(float(avg_deal_net), short=True)
        ])

    report_lines.append("## Summary by Sales Representative")
    report_lines.append("")
    report_lines.append(format_markdown_table(
        headers=["Sales Rep", "Net Sales", "Gross Sales", "Invoices", "Customers", "Avg Deal"],
        rows=summary_data
    ))
    report_lines.append("")

    # Monthly/daily breakdown for each rep
    report_lines.append(f"## Breakdown by {group_by.title()}")
    report_lines.append("")

    for rep_key, rep_data in sorted(
        sales_rep_data.items(),
        key=lambda x: x[1]["net_sales"],
        reverse=True
    ):
        rep_name = rep_key.split(":", 1)[1]
        report_lines.append(f"### {rep_name}")
        report_lines.append("")

        period_data = []
        for period in sorted(rep_data["monthly_net_sales"].keys()):
            net = rep_data["monthly_net_sales"][period]
            gross = rep_data["monthly_gross_sales"][period]
            period_data.append([
                period,
                format_currency(float(net), short=True),
                format_currency(float(gross), short=True)
            ])

        if period_data:
            report_lines.append(format_markdown_table(
                headers=["Period", "Net Sales", "Gross Sales"],
                rows=period_data
            ))
            report_lines.append("")

    # Top 10 largest deals (sorted by net sales)
    all_invoices_sorted = []
    for rep_key, rep_data in sales_rep_data.items():
        rep_name = rep_key.split(":", 1)[1]
        for inv in rep_data["invoices"]:
            all_invoices_sorted.append({
                **inv,
                "sales_rep": rep_name
            })

    all_invoices_sorted.sort(key=lambda x: x["net_sales"], reverse=True)

    if all_invoices_sorted:
        report_lines.append("## Top 10 Largest Deals")
        report_lines.append("")

        top_deals = []
        for inv in all_invoices_sorted[:10]:
            top_deals.append([
                inv["ref"],
                inv["date"],
                inv["sales_rep"],
                inv["customer"],
                format_currency(float(inv['net_sales']), short=True),
                format_currency(float(inv['gross_sales']), short=True)
            ])

        report_lines.append(format_markdown_table(
            headers=["Invoice #", "Date", "Sales Rep", "Customer", "Net Sales", "Gross Sales"],
            rows=top_deals
        ))

    return "\n".join(report_lines)


async def _find_sales_rep_id_by_name(client: KledoAPIClient, start_date, end_date, sales_rep_name: str) -> int | None:
    """Find sales rep ID by name from invoices in the date range.
    
    Args:
        client: Kledo API client
        start_date: Start date for search
        end_date: End date for search
        sales_rep_name: Sales rep name to search for (case-insensitive, partial match)
    
    Returns:
        Sales rep ID if found, None otherwise
    """
    # Fetch invoices to find sales reps
    page = 1
    per_page = 100
    search_name = sales_rep_name.lower()
    
    while True:
        response = await client.get(
            category="invoices",
            name="list",
            params={
                "per_page": per_page,
                "page": page,
                "date_from": start_date.strftime("%Y-%m-%d"),
                "date_to": end_date.strftime("%Y-%m-%d"),
                "status_ids": "3"  # Only paid invoices
            }
        )
        
        if not response or "data" not in response:
            break
        
        data = response["data"]
        if isinstance(data, dict) and "data" in data:
            items = data["data"]
            if not items:
                break
            
            # Check each invoice for matching sales rep
            for invoice in items:
                sales_person = invoice.get("sales_person") or {}
                rep_id = sales_person.get("id")
                rep_name = sales_person.get("name", "")
                
                # Check for partial match (case-insensitive)
                if rep_id and search_name in rep_name.lower():
                    return rep_id
            
            # Check if there are more pages
            if data.get("current_page", 1) >= data.get("last_page", 1):
                break
            page += 1
        else:
            break
    
    return None


async def _sales_rep_list(client: KledoAPIClient, args: dict[str, Any] = None) -> str:
    """List all sales representatives."""

    if args is None:
        args = {}

    date_from = args.get("date_from")
    date_to = args.get("date_to")

    # Parse dates if provided
    from ..utils.helpers import parse_natural_date
    start_date = None
    end_date = None
    date_range_str = "last 100 PAID invoices"

    if date_from and date_to:
        start_date = parse_natural_date(date_from)
        end_date = parse_natural_date(date_to)
        if start_date and end_date:
            date_range_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        else:
            return f"❌ Error: Could not parse dates. Provided: from={date_from}, to={date_to}"
    elif date_from or date_to:
        return "❌ Error: Both date_from and date_to are required. Please provide both or neither."

    # Fetch PAID invoices to find sales reps (status_id=3)
    all_invoices = []
    page = 1
    per_page = 100

    while True:
        params = {"per_page": per_page, "page": page, "status_ids": "3"}

        # Add date filtering if provided
        if start_date and end_date:
            params["date_from"] = start_date.strftime("%Y-%m-%d")
            params["date_to"] = end_date.strftime("%Y-%m-%d")

        response = await client.get(
            category="invoices",
            name="list",
            params=params
        )

        if not response or "data" not in response:
            break

        resp_data = response["data"]
        if isinstance(resp_data, dict) and "data" in resp_data:
            items = resp_data["data"]
            if not items:
                break
            all_invoices.extend(items)

            # Check if there are more pages
            if resp_data.get("current_page", 1) >= resp_data.get("last_page", 1):
                break
            page += 1
        else:
            break

    if not all_invoices:
        return "No paid invoices found for the specified period"

    # Collect unique sales reps using domain terminology
    sales_reps = {}
    for invoice in all_invoices:
        sales_person = invoice.get("sales_person") or {}
        rep_id = sales_person.get("id")
        rep_name = sales_person.get("name", "Unknown")

        if rep_id:
            if rep_id not in sales_reps:
                sales_reps[rep_id] = {
                    "name": rep_name,
                    "invoice_count": 0,
                    "net_sales": Decimal(0),
                    "gross_sales": Decimal(0)
                }

            sales_reps[rep_id]["invoice_count"] += 1
            net_sales = Decimal(str(invoice.get("subtotal", 0)))
            gross_sales = Decimal(str(invoice.get("amount_after_tax", 0)))
            sales_reps[rep_id]["net_sales"] += net_sales
            sales_reps[rep_id]["gross_sales"] += gross_sales

    # Build table with domain terminology
    rows = []
    for rep_id, rep_data in sorted(sales_reps.items()):
        rows.append([
            str(rep_id),
            rep_data["name"],
            str(rep_data["invoice_count"]),
            format_currency(float(rep_data['net_sales']), short=True),
            format_currency(float(rep_data['gross_sales']), short=True)
        ])

    table = format_markdown_table(
        headers=["ID", "Name", "Paid Invoices", "Net Sales", "Gross Sales"],
        rows=rows
    )

    return f"# Sales Representatives\n\n**Period**: {date_range_str}\n\n{table}\n\n_Based on PAID invoices (status_id=3 / Lunas)_\n_Net Sales (Penjualan Neto) | Gross Sales (Penjualan Bruto)_"
