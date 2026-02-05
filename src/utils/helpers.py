"""
Helper utilities for the Kledo MCP Server
"""
import hashlib
import json
import calendar
from typing import Any, Dict, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

# Jakarta timezone constant
JAKARTA_TZ = ZoneInfo("Asia/Jakarta")


def calculate_hash(data: Dict[str, Any]) -> str:
    """
    Calculate a hash for dictionary data (useful for cache keys).

    Args:
        data: Dictionary to hash

    Returns:
        MD5 hash string
    """
    # Sort keys for consistent hashing
    sorted_data = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(sorted_data.encode()).hexdigest()


def format_currency(amount: float, currency: str = "IDR", short: bool = False) -> str:
    """
    Format amount as currency.

    Args:
        amount: Amount to format
        currency: Currency code
        short: If True, use compact format (e.g., "99.2jt" instead of "Rp 99,150,720.00")

    Returns:
        Formatted currency string
    """
    if short and currency == "IDR":
        abs_amount = abs(float(amount))
        sign = "-" if float(amount) < 0 else ""
        if abs_amount >= 1_000_000_000:
            return f"{sign}{abs_amount / 1_000_000_000:.1f}M"
        elif abs_amount >= 1_000_000:
            return f"{sign}{abs_amount / 1_000_000:.1f}jt"
        elif abs_amount >= 1_000:
            return f"{sign}{abs_amount / 1_000:.0f}rb"
        else:
            return f"{sign}{abs_amount:,.0f}"
    if currency == "IDR":
        return f"Rp {amount:,.2f}"
    return f"{currency} {amount:,.2f}"


def get_jakarta_today() -> date:
    """
    Get current date in Jakarta timezone.

    Returns:
        Current date in Asia/Jakarta timezone
    """
    return datetime.now(JAKARTA_TZ).date()


def parse_indonesian_date_phrase(phrase: str) -> tuple[date | None, date | None]:
    """
    Parse Indonesian date phrases to date ranges using Jakarta timezone.

    Args:
        phrase: Indonesian date phrase (case-insensitive)

    Returns:
        Tuple of (date_from, date_to) or (None, None) if not recognized

    Supported phrases:
        - "hari ini" / "today" → (today, today)
        - "kemarin" / "yesterday" → (yesterday, yesterday)
        - "minggu ini" / "this week" → (Monday to Sunday of current week)
        - "minggu lalu" / "last week" → (Monday to Sunday of last week)
        - "bulan ini" / "this month" → (1st to last day of current month)
        - "bulan lalu" / "last month" → (1st to last day of last month)
        - "2 bulan lalu" → (1st to last day of 2 months ago)
        - "kuartal ini" / "this quarter" → (1st to last day of current quarter)
        - "semester ini" → (Jan 1 or Jul 1 to Jun 30 or Dec 31)
        - "tahun ini" / "this year" → (Jan 1 to Dec 31 of current year)
    """
    if not phrase:
        return None, None

    phrase_lower = phrase.lower().strip()
    today = get_jakarta_today()

    # Today
    if phrase_lower in ("hari ini", "today"):
        return today, today

    # Yesterday
    if phrase_lower in ("kemarin", "yesterday"):
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday

    # This week (Monday to Sunday, ISO week)
    if phrase_lower in ("minggu ini", "this week"):
        # Get Monday of current week (ISO week starts on Monday)
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return monday, sunday

    # Last week
    if phrase_lower in ("minggu lalu", "last week"):
        # Get Monday of last week
        monday_this_week = today - timedelta(days=today.weekday())
        monday_last_week = monday_this_week - timedelta(days=7)
        sunday_last_week = monday_last_week + timedelta(days=6)
        return monday_last_week, sunday_last_week

    # This month
    if phrase_lower in ("bulan ini", "this month"):
        first_day = today.replace(day=1)
        last_day_num = calendar.monthrange(today.year, today.month)[1]
        last_day = today.replace(day=last_day_num)
        return first_day, last_day

    # Last month
    if phrase_lower in ("bulan lalu", "last month"):
        first_of_this_month = today.replace(day=1)
        if first_of_this_month.month == 1:
            first_of_last_month = first_of_this_month.replace(year=first_of_this_month.year - 1, month=12)
        else:
            first_of_last_month = first_of_this_month.replace(month=first_of_this_month.month - 1)

        last_day_num = calendar.monthrange(first_of_last_month.year, first_of_last_month.month)[1]
        last_of_last_month = first_of_last_month.replace(day=last_day_num)
        return first_of_last_month, last_of_last_month

    # N months ago (e.g., "2 bulan lalu")
    if "bulan lalu" in phrase_lower:
        # Extract number
        import re
        match = re.search(r'(\d+)\s+bulan\s+lalu', phrase_lower)
        if match:
            months_ago = int(match.group(1))
            # Calculate target month
            target_month = today.month - months_ago
            target_year = today.year
            while target_month <= 0:
                target_month += 12
                target_year -= 1

            first_day = date(target_year, target_month, 1)
            last_day_num = calendar.monthrange(target_year, target_month)[1]
            last_day = date(target_year, target_month, last_day_num)
            return first_day, last_day

    # This quarter
    if phrase_lower in ("kuartal ini", "this quarter"):
        current_quarter = (today.month - 1) // 3 + 1
        first_month = (current_quarter - 1) * 3 + 1
        last_month = first_month + 2

        first_day = date(today.year, first_month, 1)
        last_day_num = calendar.monthrange(today.year, last_month)[1]
        last_day = date(today.year, last_month, last_day_num)
        return first_day, last_day

    # This semester
    if phrase_lower in ("semester ini", "this semester"):
        if today.month <= 6:
            # First semester: Jan 1 to Jun 30
            first_day = date(today.year, 1, 1)
            last_day = date(today.year, 6, 30)
        else:
            # Second semester: Jul 1 to Dec 31
            first_day = date(today.year, 7, 1)
            last_day = date(today.year, 12, 31)
        return first_day, last_day

    # This year
    if phrase_lower in ("tahun ini", "this year"):
        first_day = date(today.year, 1, 1)
        last_day = date(today.year, 12, 31)
        return first_day, last_day

    # Not recognized
    return None, None


def calculate_overdue_days(due_date_str: str, reference_date: date | None = None) -> int:
    """
    Calculate how many days an invoice is overdue.

    Args:
        due_date_str: Due date in ISO format (YYYY-MM-DD)
        reference_date: Reference date for calculation (default: today in Jakarta timezone)

    Returns:
        Number of days overdue (positive if overdue, negative if not yet due, 0 if due today)
        Returns 0 if due_date_str is empty or invalid
    """
    if not due_date_str:
        return 0

    try:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except ValueError:
        return 0

    if reference_date is None:
        reference_date = get_jakarta_today()

    return (reference_date - due_date).days


def categorize_overdue_invoices(invoices: list[dict], today: date | None = None) -> dict:
    """
    Group overdue invoices by aging buckets.

    Args:
        invoices: List of invoice dictionaries
        today: Reference date (default: today in Jakarta timezone)

    Returns:
        Dictionary with aging buckets:
        {
            "1-30": [(invoice, overdue_days), ...],
            "31-60": [(invoice, overdue_days), ...],
            "60+": [(invoice, overdue_days), ...]
        }
    """
    if today is None:
        today = get_jakarta_today()

    buckets = {
        "1-30": [],
        "31-60": [],
        "60+": []
    }

    for invoice in invoices:
        due_date_str = safe_get(invoice, "due_date", "")
        if not due_date_str:
            continue

        overdue_days = calculate_overdue_days(due_date_str, today)

        # Only include if actually overdue
        if overdue_days > 0:
            if overdue_days <= 30:
                buckets["1-30"].append((invoice, overdue_days))
            elif overdue_days <= 60:
                buckets["31-60"].append((invoice, overdue_days))
            else:
                buckets["60+"].append((invoice, overdue_days))

    return buckets


def parse_date_range(period: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse common date range expressions.

    Args:
        period: Period string like "last_month", "this_year", "2024-10"

    Returns:
        Tuple of (date_from, date_to) in YYYY-MM-DD format
    """
    today = get_jakarta_today()

    if period == "today":
        return today.isoformat(), today.isoformat()

    elif period == "this_month":
        date_from = today.replace(day=1).isoformat()
        return date_from, today.isoformat()

    elif period == "last_month":
        first_of_this_month = today.replace(day=1)
        if first_of_this_month.month == 1:
            last_month = first_of_this_month.replace(year=first_of_this_month.year - 1, month=12)
        else:
            last_month = first_of_this_month.replace(month=first_of_this_month.month - 1)

        # Last day of last month
        last_day = calendar.monthrange(last_month.year, last_month.month)[1]

        date_from = last_month.isoformat()
        date_to = last_month.replace(day=last_day).isoformat()
        return date_from, date_to

    elif period == "this_year":
        date_from = today.replace(month=1, day=1).isoformat()
        return date_from, today.isoformat()

    elif period == "last_year":
        last_year = today.year - 1
        date_from = f"{last_year}-01-01"
        date_to = f"{last_year}-12-31"
        return date_from, date_to

    # Try to parse as YYYY-MM (specific month)
    elif len(period) == 7 and period[4] == "-":
        try:
            year, month = period.split("-")
            last_day = calendar.monthrange(int(year), int(month))[1]
            return f"{period}-01", f"{period}-{last_day:02d}"
        except:
            pass

    return None, None


def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary values using dot notation.

    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., "data.items.0.name")
        default: Default value if path not found

    Returns:
        Value at path or default
    """
    keys = path.split(".")
    value = data

    try:
        for key in keys:
            if isinstance(value, list):
                value = value[int(key)]
            else:
                value = value[key]
        return value
    except (KeyError, IndexError, TypeError, ValueError):
        return default


def clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from parameters dictionary.

    Args:
        params: Parameters dictionary

    Returns:
        Cleaned dictionary
    """
    return {k: v for k, v in params.items() if v is not None}


def format_table(data: list[Dict[str, Any]], columns: list[str]) -> str:
    """
    Format data as a simple text table.

    Args:
        data: List of dictionaries
        columns: Column names to include

    Returns:
        Formatted table string
    """
    if not data:
        return "No data available"

    # Calculate column widths
    widths = {col: len(col) for col in columns}
    for row in data:
        for col in columns:
            value = str(row.get(col, ""))
            widths[col] = max(widths[col], len(value))

    # Build table
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    separator = "-+-".join("-" * widths[col] for col in columns)

    rows = []
    for row in data:
        row_str = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        rows.append(row_str)

    return "\n".join([header, separator] + rows)


def parse_natural_date(date_str: str) -> Optional[date]:
    """
    Parse natural language dates or ISO dates.

    Args:
        date_str: Date string ("2026-01-01", "today", "last month", etc.)

    Returns:
        date object or None if unparseable
    """
    if not date_str:
        return None

    today = date.today()

    # Handle natural language
    if date_str.lower() == "today":
        return today
    elif date_str.lower() == "yesterday":
        from datetime import timedelta
        return today - timedelta(days=1)
    elif date_str.lower() in ("last month", "last_month"):
        # First day of last month
        if today.month == 1:
            return date(today.year - 1, 12, 1)
        else:
            return date(today.year, today.month - 1, 1)
    elif date_str.lower() in ("this month", "this_month"):
        return date(today.year, today.month, 1)

    # Try to parse as ISO date (YYYY-MM-DD)
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        pass

    # Try to parse as YYYY-MM (month)
    try:
        return datetime.strptime(date_str, "%Y-%m").date()
    except ValueError:
        pass

    return None


def format_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """
    Format data as a monospace code block table.

    Outputs aligned columns wrapped in ``` for Telegram compatibility.
    Markdown pipe tables don't render in Telegram, so we use pre-formatted text.

    Args:
        headers: Column headers
        rows: List of row data

    Returns:
        Monospace-formatted table string wrapped in code block
    """
    if not rows:
        return "No data available"

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))

    # Build header
    header_row = "  ".join(headers[i].ljust(widths[i]) for i in range(len(headers)))
    separator = "─" * len(header_row)

    # Build rows
    table_rows = []
    for row in rows:
        cells = []
        for i in range(len(headers)):
            cell = str(row[i]) if i < len(row) else ""
            cells.append(cell.ljust(widths[i]))
        table_rows.append("  ".join(cells))

    lines = [header_row, separator] + table_rows
    return "```\n" + "\n".join(lines) + "\n```"
