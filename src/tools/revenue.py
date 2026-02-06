"""
Revenue and Receivables Tools for Kledo MCP Server
Quick revenue summaries and outstanding payment tracking
"""
from typing import Any, Dict
from mcp.types import Tool
from decimal import Decimal
from collections import defaultdict
from datetime import datetime

from ..kledo_client import KledoAPIClient
from ..utils.helpers import parse_date_range, format_currency, safe_get, format_markdown_table
from ..mappers.kledo_mapper import from_kledo_invoices, from_kledo_invoice, aggregate_financials


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
        ),
        Tool(
            name="revenue_daily_breakdown",
            description="""Get daily revenue breakdown for a period.

Shows revenue trends by day:
- Daily Net Sales (Penjualan Neto)
- Daily Tax Collected
- Daily Gross Sales
- Running totals
- Day-over-day trends

**IMPORTANT:** Only counts PAID invoices (status_id=3 / Lunas)

Perfect for answering:
- "Berapa revenue kemarin?"
- "What was yesterday's revenue?"
- "Daily trends for this month?"
- "Which days had highest sales?"

Returns daily breakdown with detailed analytics.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD or shortcuts like 'this_month', 'last_7_days')"
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
            name="outstanding_aging_report",
            description="""Get outstanding invoices grouped by age (aging report).

Shows unpaid/partially paid invoices in age buckets:
- 0-30 days (Fresh / Current)
- 30-60 days (Aging)
- 60-90 days (Overdue)
- 90+ days (CRITICAL - Way Overdue)

Includes:
- Days Sales Outstanding (DSO)
- Priority list for collections
- Total by bucket
- Customer information

Perfect for answering:
- "Siapa yang overdue?"
- "Who owes us money that's urgent?"
- "Collections priority list"
- "Days Sales Outstanding"

Sorted by age (oldest first).""",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_days": {
                        "type": "integer",
                        "description": "Show only invoices at least this many days old (default: 0)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="customer_concentration_report",
            description="""Get customer concentration analysis (80/20 Pareto analysis).

Shows business risk assessment:
- Percentage of revenue from top N customers
- 80/20 Pareto breakdown
- Concentration risk level (Green/Amber/Red)
- Diversification metrics
- Customer dependency analysis

**IMPORTANT:** Only counts PAID invoices (status_id=3 / Lunas)

Perfect for answering:
- "What % of revenue is from top customers?"
- "Are we too dependent on few customers?"
- "Business risk assessment"
- "Customer diversification status"

Risk Levels:
- GREEN: < 40% from top 5 (Healthy diversification)
- AMBER: 40-60% from top 5 (Moderate concentration)
- RED: > 60% from top 5 (High risk - needs diversification)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD or shortcuts)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD). Optional if using shortcuts."
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
    elif name == "revenue_daily_breakdown":
        return await _revenue_daily_breakdown(arguments, client)
    elif name == "outstanding_aging_report":
        return await _outstanding_aging_report(arguments, client)
    elif name == "customer_concentration_report":
        return await _customer_concentration_report(arguments, client)
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

                rows.append([inv_number, customer, date, format_currency(due, short=True)])

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
                    format_currency(due, short=True)
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
                format_currency(float(cust_data['net_sales']), short=True),
                format_currency(float(cust_data['gross_sales']), short=True),
                format_currency(float(avg_net_sales), short=True)
            ])

        result.append(format_markdown_table(
            headers=["Rank", "Customer", "Invoices", "Net Sales", "Gross Sales", "Avg Invoice"],
            rows=rows
        ))

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching customer ranking: {str(e)}"


async def _revenue_daily_breakdown(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get daily revenue breakdown for a period."""
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

        # Group invoices by date
        daily_data = defaultdict(lambda: {
            'invoices': [],
            'net_sales': Decimal(0),
            'tax_collected': Decimal(0),
            'gross_sales': Decimal(0)
        })

        for inv in invoices:
            trans_date = safe_get(inv, "trans_date", "")

            if not trans_date:
                continue

            # Convert to domain model
            try:
                financial = from_kledo_invoice(inv, include_metadata=False)
            except (ValueError, KeyError):
                continue  # Skip invalid invoices

            daily_data[trans_date]['invoices'].append(inv)
            daily_data[trans_date]['net_sales'] += financial.net_sales
            daily_data[trans_date]['tax_collected'] += financial.tax_collected
            daily_data[trans_date]['gross_sales'] += financial.gross_sales

        # Build report
        result = ["# Daily Revenue Breakdown (PAID INVOICES ONLY)\n"]
        result.append(f"**Period**: {date_from} to {date_to}\n")

        # Summary table
        result.append("## Daily Summary\n")

        rows = []
        running_net = Decimal(0)
        running_gross = Decimal(0)

        for date in sorted(daily_data.keys()):
            data_day = daily_data[date]
            running_net += data_day['net_sales']
            running_gross += data_day['gross_sales']

            rows.append([
                date,
                str(len(data_day['invoices'])),
                format_currency(float(data_day['net_sales']), short=True),
                format_currency(float(data_day['tax_collected']), short=True),
                format_currency(float(data_day['gross_sales']), short=True),
                format_currency(float(running_gross), short=True)
            ])

        result.append(format_markdown_table(
            headers=["Date", "Invoices", "Net Sales", "Tax", "Gross Sales", "Running Total"],
            rows=rows
        ))

        # Overall statistics
        result.append("\n## Overall Statistics\n")
        total_net = sum(d['net_sales'] for d in daily_data.values())
        sum(d['tax_collected'] for d in daily_data.values())
        sum(d['gross_sales'] for d in daily_data.values())
        total_invoices = sum(len(d['invoices']) for d in daily_data.values())

        avg_net = total_net / total_invoices if total_invoices > 0 else Decimal(0)
        avg_daily_net = total_net / len(daily_data) if daily_data else Decimal(0)

        result.append(f"**Total Invoices**: {total_invoices}")
        result.append(f"**Days Active**: {len(daily_data)}")
        result.append(f"**Average Per Invoice (Net)**: {format_currency(float(avg_net))}")
        result.append(f"**Average Per Day (Net)**: {format_currency(float(avg_daily_net))}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching daily revenue breakdown: {str(e)}"


async def _outstanding_aging_report(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get outstanding invoices grouped by age (aging report)."""
    min_days = args.get("min_days", 0)

    try:
        # Fetch unpaid and partially paid invoices
        all_invoices = []

        for status_id in [1, 2]:  # Unpaid and Partially Paid
            data = await client.list_invoices(
                status_id=status_id,
                per_page=100
            )
            invoices = safe_get(data, "data.data", [])
            all_invoices.extend(invoices)

        if not all_invoices:
            return "No outstanding invoices found."

        # Calculate age for each invoice
        today = datetime.now().date()
        aging_buckets = {
            '0-30': {'invoices': [], 'total': Decimal(0)},
            '30-60': {'invoices': [], 'total': Decimal(0)},
            '60-90': {'invoices': [], 'total': Decimal(0)},
            '90+': {'invoices': [], 'total': Decimal(0)}
        }

        total_outstanding = Decimal(0)
        all_days_outstanding = []

        for inv in all_invoices:
            due_amount = Decimal(str(safe_get(inv, "due", 0)))
            if due_amount <= 0:
                continue

            trans_date = safe_get(inv, "trans_date", "")
            if not trans_date:
                continue

            try:
                inv_date = datetime.strptime(trans_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue

            days_old = (today - inv_date).days

            # Filter by min_days if specified
            if days_old < min_days:
                continue

            # Categorize into age buckets
            if days_old <= 30:
                bucket = '0-30'
            elif days_old <= 60:
                bucket = '30-60'
            elif days_old <= 90:
                bucket = '60-90'
            else:
                bucket = '90+'

            aging_buckets[bucket]['invoices'].append({
                'invoice': inv,
                'days_old': days_old,
                'due': due_amount
            })
            aging_buckets[bucket]['total'] += due_amount
            total_outstanding += due_amount
            all_days_outstanding.append(days_old)

        if not all_days_outstanding:
            return f"No outstanding invoices found older than {min_days} days."

        # Calculate DSO
        dso = sum(all_days_outstanding) / len(all_days_outstanding) if all_days_outstanding else 0

        # Build report
        result = ["# Outstanding Aging Report (Piutang - Aging Analysis)\n"]
        result.append(f"**Report Date**: {today}")
        result.append(f"**Total Outstanding**: {format_currency(float(total_outstanding))}")
        result.append(f"**Days Sales Outstanding (DSO)**: {dso:.0f} days")
        result.append(f"**Total Invoices Outstanding**: {len(all_days_outstanding)}\n")

        # Show aging buckets
        for bucket_name in ['0-30', '30-60', '60-90', '90+']:
            bucket = aging_buckets[bucket_name]
            if not bucket['invoices']:
                continue

            bucket_label = {
                '0-30': 'Fresh / Current (0-30 days)',
                '30-60': 'Aging (30-60 days)',
                '60-90': 'Overdue (60-90 days)',
                '90+': '🔴 CRITICAL - Way Overdue (90+ days)'
            }[bucket_name]

            result.append(f"## {bucket_label}")
            result.append(f"**Count**: {len(bucket['invoices'])} invoices")
            result.append(f"**Total Outstanding**: {format_currency(float(bucket['total']))}\n")

            # Sort by days_old (oldest first)
            sorted_invoices = sorted(bucket['invoices'], key=lambda x: x['days_old'], reverse=True)[:10]

            rows = []
            for item in sorted_invoices:
                inv = item['invoice']
                customer = safe_get(inv, "contact.name", "Unknown")
                inv_number = safe_get(inv, "ref_number", "N/A")
                days = item['days_old']
                due = item['due']

                rows.append([
                    inv_number,
                    customer,
                    str(days),
                    format_currency(float(due), short=True)
                ])

            result.append(format_markdown_table(
                headers=["Invoice #", "Customer", "Days Old", "Outstanding"],
                rows=rows
            ))
            result.append("")

        # Priority for collections
        result.append("## Collections Priority\n")
        result.append("Focus on these invoices (90+ days overdue):\n")

        if aging_buckets['90+']['invoices']:
            critical = sorted(aging_buckets['90+']['invoices'], key=lambda x: x['due'], reverse=True)[:5]
            rows = []
            for item in critical:
                inv = item['invoice']
                customer = safe_get(inv, "contact.name", "Unknown")
                inv_number = safe_get(inv, "ref_number", "N/A")
                days = item['days_old']
                due = item['due']

                rows.append([
                    inv_number,
                    customer,
                    str(days),
                    format_currency(float(due), short=True)
                ])

            result.append(format_markdown_table(
                headers=["Invoice #", "Customer", "Days Old", "Amount Due"],
                rows=rows
            ))
        else:
            result.append("✓ No invoices over 90 days old - Good collections!")

        return "\n".join(result)

    except Exception as e:
        return f"Error generating aging report: {str(e)}"


async def _customer_concentration_report(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get customer concentration analysis (80/20 Pareto)."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

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

        # Group by customer
        customer_data = defaultdict(lambda: {
            "name": "",
            "net_sales": Decimal(0),
            "gross_sales": Decimal(0),
            "invoice_count": 0
        })

        for inv in invoices:
            contact = safe_get(inv, "contact") or {}
            contact_id = contact.get("id")

            if contact_id:
                customer_data[contact_id]["name"] = contact.get("name", "Unknown")
                customer_data[contact_id]["net_sales"] += Decimal(str(safe_get(inv, "subtotal", 0)))
                customer_data[contact_id]["gross_sales"] += Decimal(str(safe_get(inv, "amount_after_tax", 0)))
                customer_data[contact_id]["invoice_count"] += 1

        # Sort by net sales (highest first)
        sorted_customers = sorted(
            customer_data.items(),
            key=lambda x: x[1]["net_sales"],
            reverse=True
        )

        # Calculate totals
        total_net_sales = sum(c[1]["net_sales"] for c in sorted_customers)
        total_gross_sales = sum(c[1]["gross_sales"] for c in sorted_customers)

        # Calculate concentration metrics
        top_5_net = sum(c[1]["net_sales"] for c in sorted_customers[:5])
        top_10_net = sum(c[1]["net_sales"] for c in sorted_customers[:10])

        top_5_pct = (top_5_net / total_net_sales * 100) if total_net_sales > 0 else 0
        top_10_pct = (top_10_net / total_net_sales * 100) if total_net_sales > 0 else 0

        # Determine risk level
        if top_5_pct < 40:
            risk_level = "🟢 GREEN - Healthy Diversification"
        elif top_5_pct < 60:
            risk_level = "🟡 AMBER - Moderate Concentration"
        else:
            risk_level = "🔴 RED - High Risk Concentration"

        # Build report
        result = ["# Customer Concentration Report (Pareto 80/20 Analysis)\n"]
        result.append(f"**Period**: {date_from} to {date_to}")
        result.append(f"**Total Customers**: {len(customer_data)}")
        result.append(f"**Total Net Sales**: {format_currency(float(total_net_sales))}")
        result.append(f"**Total Gross Sales**: {format_currency(float(total_gross_sales))}\n")

        # Risk Assessment
        result.append("## Risk Assessment\n")
        result.append(f"**Risk Level**: {risk_level}")
        result.append(f"**Top 5 Customers**: {top_5_pct:.1f}% of revenue")
        result.append(f"**Top 10 Customers**: {top_10_pct:.1f}% of revenue\n")

        # Interpretation
        if top_5_pct < 40:
            interpretation = "Your revenue is well-distributed across many customers. This is healthy diversification and reduces business risk."
        elif top_5_pct < 60:
            interpretation = "Your top 5 customers represent a significant portion of revenue. Consider strategies to diversify the customer base."
        else:
            interpretation = "⚠️ WARNING: Your business is highly dependent on a few customers. This represents significant risk. Prioritize acquiring new customers and diversifying revenue sources."

        result.append(f"**Interpretation**: {interpretation}\n")

        # Top customers table
        result.append("## Top Customers by Revenue\n")

        rows = []
        cumulative_pct = Decimal(0)

        for i, (customer_id, cust_data) in enumerate(sorted_customers[:10], 1):
            pct_of_total = (cust_data["net_sales"] / total_net_sales * 100) if total_net_sales > 0 else 0
            cumulative_pct += Decimal(str(pct_of_total))

            rows.append([
                str(i),
                cust_data["name"],
                format_currency(float(cust_data['net_sales']), short=True),
                f"{pct_of_total:.1f}%",
                f"{float(cumulative_pct):.1f}%"
            ])

        result.append(format_markdown_table(
            headers=["Rank", "Customer", "Net Sales", "% of Total", "Cumulative %"],
            rows=rows
        ))

        # Pareto insight
        result.append("\n## Pareto Insight (80/20 Rule)\n")

        # Find how many customers make up 80% of revenue
        cumulative = Decimal(0)
        customers_for_80_pct = 0

        for customer_id, cust_data in sorted_customers:
            cumulative += cust_data["net_sales"]
            customers_for_80_pct += 1

            if cumulative / total_net_sales * 100 >= 80:
                break

        pct_of_customers = (customers_for_80_pct / len(customer_data) * 100) if customer_data else 0

        result.append(f"**80% of revenue comes from**: {customers_for_80_pct} customers ({pct_of_customers:.1f}% of total customers)")
        result.append("**Healthy ratio**: 20% of customers = 80% of revenue")

        if customers_for_80_pct <= len(customer_data) * 0.2:
            result.append("✓ This matches the ideal 80/20 ratio - Well-diversified customer base")
        elif customers_for_80_pct <= len(customer_data) * 0.3:
            result.append("⚠️ More customers needed for 80% of revenue - Consider acquisition strategy")
        else:
            result.append("🔴 Too many customers for 80% of revenue - Concentration risk")

        return "\n".join(result)

    except Exception as e:
        return f"Error generating concentration report: {str(e)}"
