"""
Analytics tools for period-over-period comparison.
Enables comparison of revenue and outstanding across time periods.
"""
from typing import Any, Dict
from mcp.types import Tool
from collections import defaultdict
import asyncio
import calendar
from datetime import datetime, date

from ..kledo_client import KledoAPIClient
from ..utils.helpers import (
    parse_indonesian_date_phrase,
    format_currency,
    safe_get,
    get_jakarta_today,
    JAKARTA_TZ,
    format_markdown_table,
    parse_date_range
)
from .financial import _fetch_all_invoices


# Indonesian month names for display
INDONESIAN_MONTHS = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]


def get_tools() -> list[Tool]:
    """Get list of analytics comparison tools."""
    return [
        Tool(
            name="analytics_compare_revenue",
            description=(
                "Compare revenue (paid invoices) between two periods. "
                "Only paid invoices (status_id=3) count as revenue. "
                "Single period = no comparison. "
                "Indonesian hints: 'revenue bulan ini vs bulan lalu', "
                "'penjualan kuartal ini vs kuartal lalu', "
                "'revenue bulan ini' (single period only)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": (
                            "Current period phrase: 'bulan ini', 'kuartal ini', "
                            "'tahun ini', '2026-01', or YYYY-MM-DD"
                        )
                    },
                    "compare_to": {
                        "type": "string",
                        "description": (
                            "Comparison period phrase: 'bulan lalu', 'kuartal lalu'. "
                            "If omitted, shows only the current period (NO automatic comparison)."
                        )
                    },
                    "per_sales": {
                        "type": "boolean",
                        "description": "If true, break down by sales rep"
                    }
                },
                "required": ["period"]
            }
        ),
        Tool(
            name="analytics_compare_outstanding",
            description=(
                "Compare outstanding (unpaid invoices) between two periods. "
                "Status_id != 3 = outstanding. "
                "Indonesian hints: 'outstanding bulan ini vs bulan lalu', "
                "'piutang kuartal ini vs kuartal lalu', "
                "'outstanding bulan ini' (single period only)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": (
                            "Current period phrase: 'bulan ini', 'kuartal ini', "
                            "'tahun ini', '2026-01', or YYYY-MM-DD"
                        )
                    },
                    "compare_to": {
                        "type": "string",
                        "description": (
                            "Comparison period phrase: 'bulan lalu', 'kuartal lalu'. "
                            "If omitted, shows only the current period."
                        )
                    },
                    "per_sales": {
                        "type": "boolean",
                        "description": "If true, break down by sales rep"
                    }
                },
                "required": ["period"]
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:
    """Handle analytics tool calls."""
    if name == "analytics_compare_revenue":
        return await _compare_revenue(arguments, client)
    elif name == "analytics_compare_outstanding":
        return await _compare_outstanding(arguments, client)
    else:
        return f"Unknown analytics tool: {name}"


def _resolve_period(phrase: str) -> tuple[str, str, str]:
    """
    Resolve a period phrase to date range and display name.

    Args:
        phrase: Period phrase (Indonesian, English, or YYYY-MM)

    Returns:
        Tuple of (date_from_str, date_to_str, display_name)
        where display_name is human-readable like "Januari 2026", "Q1 2026"
    """
    # Try Indonesian date phrase first
    date_from, date_to = parse_indonesian_date_phrase(phrase)

    if date_from and date_to:
        # Create display name from resolved dates
        if date_from == date_to:
            # Single day
            display_name = date_from.strftime("%d %B %Y")
        elif date_from.year == date_to.year and date_from.month == date_to.month:
            # Single month
            month_name = INDONESIAN_MONTHS[date_from.month - 1]
            display_name = f"{month_name} {date_from.year}"
        elif date_from.day == 1 and date_to.day == calendar.monthrange(date_to.year, date_to.month)[1]:
            # Detect quarter
            quarter = (date_from.month - 1) // 3 + 1
            if date_from.month == (quarter - 1) * 3 + 1 and date_to.month == quarter * 3:
                display_name = f"Q{quarter} {date_from.year}"
            else:
                # Multi-month range
                from_month = INDONESIAN_MONTHS[date_from.month - 1]
                to_month = INDONESIAN_MONTHS[date_to.month - 1]
                if date_from.year == date_to.year:
                    display_name = f"{from_month}-{to_month} {date_from.year}"
                else:
                    display_name = f"{from_month} {date_from.year} - {to_month} {date_to.year}"
        elif date_from.month == 1 and date_to.month == 12 and date_from.day == 1 and date_to.day == 31:
            # Full year
            display_name = f"Tahun {date_from.year}"
        else:
            # Generic range
            display_name = f"{date_from.isoformat()} to {date_to.isoformat()}"

        return date_from.isoformat(), date_to.isoformat(), display_name

    # Try English shortcuts
    date_from_str, date_to_str = parse_date_range(phrase)
    if date_from_str and date_to_str:
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
        date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()

        # Create display name
        if date_from.year == date_to.year and date_from.month == date_to.month:
            month_name = INDONESIAN_MONTHS[date_from.month - 1]
            display_name = f"{month_name} {date_from.year}"
        else:
            display_name = f"{date_from_str} to {date_to_str}"

        return date_from_str, date_to_str, display_name

    # Try YYYY-MM parsing
    if len(phrase) == 7 and phrase[4] == "-":
        try:
            year, month = phrase.split("-")
            year = int(year)
            month = int(month)
            last_day = calendar.monthrange(year, month)[1]

            date_from_str = f"{phrase}-01"
            date_to_str = f"{phrase}-{last_day:02d}"

            month_name = INDONESIAN_MONTHS[month - 1]
            display_name = f"{month_name} {year}"

            return date_from_str, date_to_str, display_name
        except (ValueError, IndexError):
            pass

    # Fallback: treat as single date
    try:
        single_date = datetime.strptime(phrase, "%Y-%m-%d").date()
        return single_date.isoformat(), single_date.isoformat(), single_date.strftime("%d %B %Y")
    except ValueError:
        # Final fallback: use today
        today = get_jakarta_today()
        return today.isoformat(), today.isoformat(), "Hari Ini"


def _aggregate_period_data(invoices: list, per_sales: bool = False) -> dict:
    """
    Aggregate invoice data for a period.

    Args:
        invoices: List of invoice dictionaries
        per_sales: If True, break down by sales person

    Returns:
        Dictionary with aggregated data:
        {
            "revenue": float,       # sum of subtotal where status_id == 3 (PAID)
            "outstanding": float,   # sum of due where status_id != 3
            "count": int,           # total invoice count
            "paid_count": int,      # count of status_id == 3
            "by_sales": {           # only if per_sales=True
                "Kevin": {"revenue": float, "outstanding": float, "count": int},
                ...
            }
        }
    """
    result = {
        "revenue": 0.0,
        "outstanding": 0.0,
        "count": 0,
        "paid_count": 0
    }

    if per_sales:
        result["by_sales"] = defaultdict(lambda: {"revenue": 0.0, "outstanding": 0.0, "count": 0})

    for inv in invoices:
        status_id = safe_get(inv, "status_id", 1)
        subtotal = safe_get(inv, "subtotal", 0)
        due = safe_get(inv, "due", 0)

        result["count"] += 1

        if status_id == 3:
            # Paid invoice = revenue
            result["revenue"] += subtotal
            result["paid_count"] += 1
        else:
            # Unpaid = outstanding
            result["outstanding"] += due

        if per_sales:
            sales_person = inv.get("sales_person")
            if sales_person and isinstance(sales_person, dict):
                sp_name = sales_person.get("name", "(Tidak Ada Sales)")
            else:
                sp_name = "(Tidak Ada Sales)"

            result["by_sales"][sp_name]["count"] += 1
            if status_id == 3:
                result["by_sales"][sp_name]["revenue"] += subtotal
            else:
                result["by_sales"][sp_name]["outstanding"] += due

    return result


async def _compare_revenue(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """
    Compare revenue between two periods.

    Args:
        args: Tool arguments with period, compare_to, per_sales
        client: Kledo API client

    Returns:
        Formatted comparison string
    """
    period = args.get("period")
    compare_to = args.get("compare_to")
    per_sales = args.get("per_sales", False)

    if not period:
        return "Error: period parameter is required"

    # Resolve periods
    from1, to1, name1 = _resolve_period(period)

    if compare_to:
        from2, to2, name2 = _resolve_period(compare_to)

        # Fetch both periods in parallel
        inv_current, inv_comparison = await asyncio.gather(
            _fetch_all_invoices(client, from1, to1),
            _fetch_all_invoices(client, from2, to2)
        )

        # Aggregate both periods
        data_current = _aggregate_period_data(inv_current, per_sales)
        data_comparison = _aggregate_period_data(inv_comparison, per_sales)

        # Format comparison
        result = []
        result.append(f"## Revenue Comparison: {name1} vs {name2}\n")

        # Revenue comparison
        rev1 = data_current["revenue"]
        rev2 = data_comparison["revenue"]

        if rev2 > 0:
            rev_change_pct = ((rev1 - rev2) / rev2) * 100
            rev_change_str = f"{rev_change_pct:+.1f}%"
        else:
            rev_change_str = "N/A"

        result.append("**Revenue (Paid):**")
        result.append(f"{name1}: {format_currency(rev1, short=True)} | {name2}: {format_currency(rev2, short=True)} ({rev_change_str})")
        result.append("")

        # Invoice count
        count1 = data_current["paid_count"]
        count2 = data_comparison["paid_count"]

        result.append("**Invoice Count (Paid):**")
        result.append(f"{name1}: {count1} | {name2}: {count2}")

        # Per-sales breakdown if requested
        if per_sales and data_current.get("by_sales"):
            result.append("\n### Per Sales Rep:\n")

            # Combine sales reps from both periods
            all_sales = set(data_current["by_sales"].keys()) | set(data_comparison["by_sales"].keys())

            rows = []
            for sp_name in sorted(all_sales):
                sp1 = data_current["by_sales"].get(sp_name, {"revenue": 0, "count": 0})
                sp2 = data_comparison["by_sales"].get(sp_name, {"revenue": 0, "count": 0})

                rev1_sp = sp1["revenue"]
                rev2_sp = sp2["revenue"]

                if rev2_sp > 0:
                    change_pct = ((rev1_sp - rev2_sp) / rev2_sp) * 100
                    change_str = f"{change_pct:+.1f}%"
                else:
                    change_str = "N/A"

                rows.append([
                    sp_name,
                    format_currency(rev1_sp, short=True),
                    format_currency(rev2_sp, short=True),
                    change_str
                ])

            result.append(format_markdown_table(
                ["Sales Rep", name1, name2, "Change"],
                rows
            ))

        return "\n".join(result)

    else:
        # Single period - no comparison
        inv_current = await _fetch_all_invoices(client, from1, to1)
        data_current = _aggregate_period_data(inv_current, per_sales)

        result = []
        result.append(f"## Revenue: {name1}\n")

        rev = data_current["revenue"]
        paid_count = data_current["paid_count"]

        result.append(f"**Revenue (Paid):** {format_currency(rev, short=True)}")
        result.append(f"**Invoice Count (Paid):** {paid_count}")

        # Per-sales breakdown if requested
        if per_sales and data_current.get("by_sales"):
            result.append("\n### Per Sales Rep:\n")

            rows = []
            for sp_name, sp_data in sorted(data_current["by_sales"].items()):
                rows.append([
                    sp_name,
                    format_currency(sp_data["revenue"], short=True),
                    str(sp_data["count"])
                ])

            result.append(format_markdown_table(
                ["Sales Rep", "Revenue", "Invoices"],
                rows
            ))

        return "\n".join(result)


async def _compare_outstanding(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """
    Compare outstanding between two periods.

    Args:
        args: Tool arguments with period, compare_to, per_sales
        client: Kledo API client

    Returns:
        Formatted comparison string
    """
    period = args.get("period")
    compare_to = args.get("compare_to")
    per_sales = args.get("per_sales", False)

    if not period:
        return "Error: period parameter is required"

    # Resolve periods
    from1, to1, name1 = _resolve_period(period)

    if compare_to:
        from2, to2, name2 = _resolve_period(compare_to)

        # Fetch both periods in parallel
        inv_current, inv_comparison = await asyncio.gather(
            _fetch_all_invoices(client, from1, to1),
            _fetch_all_invoices(client, from2, to2)
        )

        # Aggregate both periods
        data_current = _aggregate_period_data(inv_current, per_sales)
        data_comparison = _aggregate_period_data(inv_comparison, per_sales)

        # Format comparison
        result = []
        result.append(f"## Outstanding Comparison: {name1} vs {name2}\n")

        # Outstanding comparison
        out1 = data_current["outstanding"]
        out2 = data_comparison["outstanding"]

        if out2 > 0:
            out_change_pct = ((out1 - out2) / out2) * 100
            out_change_str = f"{out_change_pct:+.1f}%"
        else:
            out_change_str = "N/A"

        result.append("**Outstanding (Unpaid):**")
        result.append(f"{name1}: {format_currency(out1, short=True)} | {name2}: {format_currency(out2, short=True)} ({out_change_str})")
        result.append("")

        # Invoice count (unpaid)
        unpaid_count1 = data_current["count"] - data_current["paid_count"]
        unpaid_count2 = data_comparison["count"] - data_comparison["paid_count"]

        result.append("**Invoice Count (Unpaid):**")
        result.append(f"{name1}: {unpaid_count1} | {name2}: {unpaid_count2}")

        # Per-sales breakdown if requested
        if per_sales and data_current.get("by_sales"):
            result.append("\n### Per Sales Rep:\n")

            # Combine sales reps from both periods
            all_sales = set(data_current["by_sales"].keys()) | set(data_comparison["by_sales"].keys())

            rows = []
            for sp_name in sorted(all_sales):
                sp1 = data_current["by_sales"].get(sp_name, {"outstanding": 0, "count": 0})
                sp2 = data_comparison["by_sales"].get(sp_name, {"outstanding": 0, "count": 0})

                out1_sp = sp1["outstanding"]
                out2_sp = sp2["outstanding"]

                if out2_sp > 0:
                    change_pct = ((out1_sp - out2_sp) / out2_sp) * 100
                    change_str = f"{change_pct:+.1f}%"
                else:
                    change_str = "N/A"

                rows.append([
                    sp_name,
                    format_currency(out1_sp, short=True),
                    format_currency(out2_sp, short=True),
                    change_str
                ])

            result.append(format_markdown_table(
                ["Sales Rep", name1, name2, "Change"],
                rows
            ))

        return "\n".join(result)

    else:
        # Single period - no comparison
        inv_current = await _fetch_all_invoices(client, from1, to1)
        data_current = _aggregate_period_data(inv_current, per_sales)

        result = []
        result.append(f"## Outstanding: {name1}\n")

        out = data_current["outstanding"]
        unpaid_count = data_current["count"] - data_current["paid_count"]

        result.append(f"**Outstanding (Unpaid):** {format_currency(out, short=True)}")
        result.append(f"**Invoice Count (Unpaid):** {unpaid_count}")

        # Per-sales breakdown if requested
        if per_sales and data_current.get("by_sales"):
            result.append("\n### Per Sales Rep:\n")

            rows = []
            for sp_name, sp_data in sorted(data_current["by_sales"].items()):
                rows.append([
                    sp_name,
                    format_currency(sp_data["outstanding"], short=True),
                    str(sp_data["count"])
                ])

            result.append(format_markdown_table(
                ["Sales Rep", "Outstanding", "Invoices"],
                rows
            ))

        return "\n".join(result)
