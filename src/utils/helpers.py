"""
Helper utilities for the Kledo MCP Server
"""
import hashlib
import json
from typing import Any, Dict, Optional
from datetime import datetime, date
from decimal import Decimal


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


def format_currency(amount: float, currency: str = "IDR") -> str:
    """
    Format amount as currency.

    Args:
        amount: Amount to format
        currency: Currency code

    Returns:
        Formatted currency string
    """
    if currency == "IDR":
        return f"Rp {amount:,.2f}"
    return f"{currency} {amount:,.2f}"


def parse_date_range(period: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse common date range expressions.

    Args:
        period: Period string like "last_month", "this_year", "2024-10"

    Returns:
        Tuple of (date_from, date_to) in YYYY-MM-DD format
    """
    today = date.today()

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
        if today.month == 1:
            last_day = 31
        else:
            import calendar
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
            import calendar
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
    Format data as a Markdown table.

    Args:
        headers: Column headers
        rows: List of row data

    Returns:
        Markdown-formatted table string
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
    header_row = "| " + " | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))) + " |"
    separator = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"

    # Build rows
    table_rows = []
    for row in rows:
        row_str = "| " + " | ".join(str(row[i]).ljust(widths[i]) if i < len(row) else " " * widths[i] for i in range(len(headers))) + " |"
        table_rows.append(row_str)

    return "\n".join([header_row, separator] + table_rows)
