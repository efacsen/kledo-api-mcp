"""
Commission calculation tools for sales reps.
Enables tiered commission calculation based on paid invoices (cash basis).
"""
from typing import Any, Dict
from mcp.types import Tool
from collections import defaultdict
from datetime import datetime
import calendar

from ..kledo_client import KledoAPIClient
from ..utils.helpers import (
    parse_indonesian_date_phrase,
    format_currency,
    safe_get,
    get_jakarta_today,
    format_markdown_table,
    parse_date_range
)
from .financial import _fetch_all_invoices
from .analytics import _resolve_period


# Default tiered commission structure (hardcoded per CONTEXT.md)
# Progressive tiers like tax brackets - each rate applies ONLY to revenue in that bracket
DEFAULT_COMMISSION_TIERS = [
    {"threshold": 0, "rate": 0.01},            # 1% on first 100M
    {"threshold": 100_000_000, "rate": 0.02},   # 2% on 100M-300M
    {"threshold": 300_000_000, "rate": 0.03},   # 3% on 300M+
]


def calculate_tiered_commission(paid_revenue: float, tiers: list = None, flat_rate: float = None) -> dict:
    """
    Calculate tiered commission on paid revenue.

    Args:
        paid_revenue: Total paid invoice amount (subtotal before tax)
        tiers: Custom tier structure (defaults to DEFAULT_COMMISSION_TIERS)
        flat_rate: If provided, override tiers with flat rate (per-query override)

    Returns:
        {
            "total_commission": float,
            "breakdown": [{"tier": int, "range": str, "amount": float, "rate": float, "commission": float}],
            "effective_rate": float  # total_commission / paid_revenue
        }
    """
    # Inline flat rate override (CONTEXT.md: "dengan rate 3%")
    if flat_rate is not None:
        commission = paid_revenue * flat_rate
        return {
            "total_commission": commission,
            "breakdown": [{
                "tier": 1,
                "range": "Flat rate",
                "amount": paid_revenue,
                "rate": flat_rate,
                "commission": commission
            }],
            "effective_rate": flat_rate
        }

    # Default tiered calculation
    if tiers is None:
        tiers = DEFAULT_COMMISSION_TIERS

    total_commission = 0.0
    breakdown = []
    remaining = paid_revenue

    for idx, tier in enumerate(tiers):
        if remaining <= 0:
            break

        # Calculate amount in this tier
        next_threshold = tiers[idx + 1]["threshold"] if idx + 1 < len(tiers) else float('inf')
        tier_amount = min(remaining, next_threshold - tier["threshold"])

        if tier_amount <= 0:
            continue

        # Calculate commission for this tier
        tier_commission = tier_amount * tier["rate"]
        total_commission += tier_commission

        # Format range for display
        if idx + 1 < len(tiers):
            # Not the last tier
            range_str = f"{tier['threshold'] // 1_000_000}jt - {next_threshold // 1_000_000}jt"
        else:
            # Last tier
            range_str = f"{tier['threshold'] // 1_000_000}jt+"

        breakdown.append({
            "tier": idx + 1,
            "range": range_str,
            "amount": tier_amount,
            "rate": tier["rate"],
            "commission": tier_commission
        })

        remaining -= tier_amount

    effective_rate = total_commission / paid_revenue if paid_revenue > 0 else 0.0

    return {
        "total_commission": total_commission,
        "breakdown": breakdown,
        "effective_rate": effective_rate
    }


def get_tools() -> list[Tool]:
    """Get list of commission calculation tools."""
    return [
        Tool(
            name="commission_calculate",
            description=(
                "Calculate commission for a specific sales person based on paid invoices only (cash basis). "
                "Commission is calculated on subtotal (before tax). "
                "Supports tiered rates (1% on first 100M, 2% on 100M-300M, 3% on 300M+) or flat rate override. "
                "Indonesian hints: 'komisi Kevin bulan ini', 'komisi sales Elmo bulan lalu', "
                "'komisi Kevin dengan rate 3%', 'hitung komisi Kevin'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": (
                            "Period phrase: 'bulan ini', 'bulan lalu', '2026-01', or YYYY-MM-DD"
                        )
                    },
                    "sales_person_name": {
                        "type": "string",
                        "description": "Sales rep name, e.g., 'Kevin', 'Elmo', 'Rabian'"
                    },
                    "flat_rate": {
                        "type": "number",
                        "description": (
                            "Override tiered commission with flat rate (e.g., 0.03 for 3%). "
                            "If provided, applies flat rate to entire revenue instead of tiered brackets."
                        )
                    }
                },
                "required": ["period", "sales_person_name"]
            }
        ),
        Tool(
            name="commission_report",
            description=(
                "Get commission breakdown for ALL sales reps in a period. "
                "Shows revenue, commission, and tier breakdown for each rep. "
                "Indonesian hints: 'komisi per sales bulan ini', 'commission breakdown bulan lalu', "
                "'laporan komisi', 'komisi seluruh sales'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Period phrase: 'bulan ini', 'bulan lalu', '2026-01'"
                    },
                    "flat_rate": {
                        "type": "number",
                        "description": "Override tiered commission with flat rate for all reps (e.g., 0.03 for 3%)"
                    }
                },
                "required": ["period"]
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:
    """Handle commission tool calls."""
    if name == "commission_calculate":
        return await _commission_calculate(arguments, client)
    elif name == "commission_report":
        return await _commission_report(arguments, client)
    else:
        return f"Unknown commission tool: {name}"


async def _fetch_paid_invoices_for_period(client: KledoAPIClient, period_phrase: str) -> tuple[list, str, str, str]:
    """
    Fetch paid invoices for a period with payment date awareness.

    Args:
        client: Kledo API client
        period_phrase: Period phrase (Indonesian, English, or YYYY-MM)

    Returns:
        Tuple of (paid_invoices, date_from, date_to, display_name)
    """
    # Resolve period phrase to date range
    date_from, date_to, display_name = _resolve_period(period_phrase)

    # Fetch all invoices for the date range
    all_invoices = await _fetch_all_invoices(client, date_from, date_to)

    # Filter to ONLY status_id == 3 (paid invoices)
    paid_invoices = []
    for inv in all_invoices:
        status_id = safe_get(inv, "status_id", 1)

        if status_id == 3:
            # Check if payment_date is available and within period
            payment_date = safe_get(inv, "payment_date") or safe_get(inv, "paid_date")

            if payment_date:
                # Verify payment date falls within the period
                if date_from <= payment_date <= date_to:
                    paid_invoices.append(inv)
            else:
                # No payment_date field - fall back to including the invoice
                # (less accurate but functional)
                paid_invoices.append(inv)

    return paid_invoices, date_from, date_to, display_name


async def _commission_calculate(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """
    Calculate commission for a specific sales person.

    Args:
        args: Tool arguments with period, sales_person_name, flat_rate
        client: Kledo API client

    Returns:
        Formatted commission report string
    """
    period = args.get("period")
    sales_person_name = args.get("sales_person_name", "").strip()
    flat_rate = args.get("flat_rate")

    if not period:
        return "Error: period parameter is required"
    if not sales_person_name:
        return "Error: sales_person_name parameter is required"

    # Fetch paid invoices for period
    paid_invoices, date_from, date_to, display_name = await _fetch_paid_invoices_for_period(client, period)

    # Filter to invoices where sales_person.name matches (case-insensitive partial match)
    sales_invoices = []
    for inv in paid_invoices:
        sales_person = inv.get("sales_person")
        if sales_person and isinstance(sales_person, dict):
            sp_name = sales_person.get("name", "")
            if sp_name and sales_person_name.lower() in sp_name.lower():
                sales_invoices.append(inv)

    if not sales_invoices:
        return f"Tidak ada invoice yang sudah dibayar untuk {sales_person_name} di {display_name}"

    # Sum subtotal (NOT amount_after_tax) for commission base
    commission_base = 0.0
    for inv in sales_invoices:
        subtotal = safe_get(inv, "subtotal", 0)
        commission_base += subtotal

    # Calculate commission
    commission_data = calculate_tiered_commission(commission_base, flat_rate=flat_rate)

    # Format response
    result = []
    result.append(f"## Komisi Sales: {sales_person_name} - {display_name}\n")

    result.append(f"**Revenue (Paid):** {format_currency(commission_base, short=True)} (subtotal, sebelum pajak)")
    result.append(f"**Total Komisi:** {format_currency(commission_data['total_commission'], short=True)} ({commission_data['effective_rate']:.2%})")
    result.append(f"**Invoice Count:** {len(sales_invoices)}\n")

    # Tier breakdown
    result.append("### Tier Breakdown:\n")
    result.append("```")

    rows = []
    for tier in commission_data["breakdown"]:
        rows.append([
            str(tier["tier"]),
            tier["range"],
            format_currency(tier["amount"], short=True),
            f"{tier['rate']:.1%}",
            format_currency(tier["commission"], short=True)
        ])

    result.append(format_markdown_table(
        ["Tier", "Range", "Revenue", "Rate", "Komisi"],
        rows
    ))
    result.append("```")

    result.append("\n_*Komisi dihitung dari revenue setelah customer bayar (cash basis), sebelum pajak_")

    return "\n".join(result)


async def _commission_report(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """
    Get commission breakdown for ALL sales reps in a period.

    Args:
        args: Tool arguments with period, flat_rate
        client: Kledo API client

    Returns:
        Formatted commission report for all reps
    """
    period = args.get("period")
    flat_rate = args.get("flat_rate")

    if not period:
        return "Error: period parameter is required"

    # Fetch paid invoices for period
    paid_invoices, date_from, date_to, display_name = await _fetch_paid_invoices_for_period(client, period)

    if not paid_invoices:
        return f"Tidak ada invoice yang sudah dibayar di {display_name}"

    # Group by sales person name
    sales_data = defaultdict(lambda: {"revenue": 0.0, "invoices": []})

    for inv in paid_invoices:
        sales_person = inv.get("sales_person")
        if sales_person and isinstance(sales_person, dict):
            sp_name = sales_person.get("name", "(Tidak Ada Sales)")
        else:
            sp_name = "(Tidak Ada Sales)"

        subtotal = safe_get(inv, "subtotal", 0)
        sales_data[sp_name]["revenue"] += subtotal
        sales_data[sp_name]["invoices"].append(inv)

    # Calculate commission for each rep
    commission_results = []
    for sp_name, data in sales_data.items():
        comm_data = calculate_tiered_commission(data["revenue"], flat_rate=flat_rate)
        commission_results.append({
            "name": sp_name,
            "revenue": data["revenue"],
            "commission": comm_data["total_commission"],
            "effective_rate": comm_data["effective_rate"],
            "invoice_count": len(data["invoices"]),
            "breakdown": comm_data["breakdown"]
        })

    # Sort by revenue descending
    commission_results.sort(key=lambda x: x["revenue"], reverse=True)

    # Format summary table
    result = []
    result.append(f"## Laporan Komisi per Sales - {display_name}\n")

    result.append("### Summary:\n")
    result.append("```")

    summary_rows = []
    for item in commission_results:
        summary_rows.append([
            item["name"],
            format_currency(item["revenue"], short=True),
            format_currency(item["commission"], short=True),
            f"{item['effective_rate']:.2%}"
        ])

    result.append(format_markdown_table(
        ["Sales", "Revenue", "Komisi", "Rate"],
        summary_rows
    ))
    result.append("```")

    # Per-rep tier breakdown (top 10 cap)
    result.append("\n### Detail Breakdown per Sales:\n")

    for idx, item in enumerate(commission_results[:10], 1):
        result.append(f"\n**{idx}. {item['name']}** - {format_currency(item['revenue'], short=True)}")
        result.append("```")

        tier_rows = []
        for tier in item["breakdown"]:
            tier_rows.append([
                str(tier["tier"]),
                tier["range"],
                format_currency(tier["amount"], short=True),
                f"{tier['rate']:.1%}",
                format_currency(tier["commission"], short=True)
            ])

        result.append(format_markdown_table(
            ["Tier", "Range", "Revenue", "Rate", "Komisi"],
            tier_rows
        ))
        result.append("```")

    if len(commission_results) > 10:
        result.append(f"\n_*Showing top 10 of {len(commission_results)} sales reps_")

    # Grand total
    total_revenue = sum(item["revenue"] for item in commission_results)
    total_commission = sum(item["commission"] for item in commission_results)
    avg_rate = total_commission / total_revenue if total_revenue > 0 else 0.0

    result.append("\n### Grand Total:\n")
    result.append(f"**Total Revenue:** {format_currency(total_revenue, short=True)}")
    result.append(f"**Total Komisi:** {format_currency(total_commission, short=True)}")
    result.append(f"**Average Rate:** {avg_rate:.2%}")

    result.append("\n_*Komisi dihitung dari revenue setelah customer bayar (cash basis), sebelum pajak_")

    return "\n".join(result)
