"""
Extended natural language date parsing.

Handles both calendar-based (ISO week/month boundaries) and
rolling window date ranges for business queries.
"""

import re
from datetime import date, timedelta
from calendar import monthrange


def parse_natural_date(phrase: str) -> tuple[date, date] | None:
    """
    Parse a natural language date phrase into a date range.

    Supports:
    - Calendar-based: "last week", "this month", "q1", etc.
    - Rolling windows: "7 days", "30 days", etc.
    - Bilingual: English and Indonesian phrases

    Args:
        phrase: Natural language date phrase

    Returns:
        Tuple of (start_date, end_date) or None if phrase doesn't match
    """
    phrase_lower = phrase.lower().strip()
    today = date.today()

    # Calendar-based patterns

    # Last week (previous ISO week, Monday to Sunday)
    if phrase_lower in ("last week", "minggu lalu", "minggu kemarin"):
        iso_year, iso_week, iso_weekday = today.isocalendar()
        monday = today - timedelta(days=iso_weekday - 1)
        prev_monday = monday - timedelta(weeks=1)
        prev_sunday = prev_monday + timedelta(days=6)
        return (prev_monday, prev_sunday)

    # This week (current ISO week start to today)
    if phrase_lower in ("this week", "minggu ini"):
        iso_year, iso_week, iso_weekday = today.isocalendar()
        monday = today - timedelta(days=iso_weekday - 1)
        return (monday, today)

    # This month (first of month to today)
    if phrase_lower in ("this month", "bulan ini"):
        first_of_month = today.replace(day=1)
        return (first_of_month, today)

    # Last month (full previous month)
    if phrase_lower in ("last month", "bulan lalu", "bulan kemarin"):
        first_of_current = today.replace(day=1)
        last_of_prev = first_of_current - timedelta(days=1)
        first_of_prev = last_of_prev.replace(day=1)
        return (first_of_prev, last_of_prev)

    # This year (Jan 1 to today)
    if phrase_lower in ("this year", "tahun ini"):
        first_of_year = today.replace(month=1, day=1)
        return (first_of_year, today)

    # Last year (full previous year)
    if phrase_lower in ("last year", "tahun lalu", "tahun kemarin"):
        prev_year = today.year - 1
        first_of_prev_year = date(prev_year, 1, 1)
        last_of_prev_year = date(prev_year, 12, 31)
        return (first_of_prev_year, last_of_prev_year)

    # Quarters - using current year
    year = today.year

    # Q1
    if phrase_lower in ("q1", "kuartal 1", "quarter 1"):
        return (date(year, 1, 1), date(year, 3, 31))

    # Q2
    if phrase_lower in ("q2", "kuartal 2", "quarter 2"):
        return (date(year, 4, 1), date(year, 6, 30))

    # Q3
    if phrase_lower in ("q3", "kuartal 3", "quarter 3"):
        return (date(year, 7, 1), date(year, 9, 30))

    # Q4
    if phrase_lower in ("q4", "kuartal 4", "quarter 4"):
        return (date(year, 10, 1), date(year, 12, 31))

    # Rolling windows (from today backward)

    # Pattern: N days (numeric)
    days_match = re.match(r"(\d+)\s*(?:days?|hari)", phrase_lower)
    if days_match:
        days = int(days_match.group(1))
        start = today - timedelta(days=days)
        return (start, today)

    # Indonesian number words for common periods
    indonesian_numbers = {
        "tujuh": 7,
        "sepuluh": 10,
        "empat belas": 14,
        "lima belas": 15,
        "dua puluh": 20,
        "tiga puluh": 30,
        "enam puluh": 60,
        "sembilan puluh": 90,
    }

    for word, num in indonesian_numbers.items():
        if f"{word} hari" in phrase_lower:
            start = today - timedelta(days=num)
            return (start, today)

    # English words for common periods
    english_numbers = {
        "seven": 7,
        "fourteen": 14,
        "thirty": 30,
        "sixty": 60,
        "ninety": 90,
    }

    for word, num in english_numbers.items():
        if f"{word} days" in phrase_lower:
            start = today - timedelta(days=num)
            return (start, today)

    # Yesterday
    if phrase_lower in ("yesterday", "kemarin"):
        yesterday = today - timedelta(days=1)
        return (yesterday, yesterday)

    # Today
    if phrase_lower in ("today", "hari ini"):
        return (today, today)

    # No match
    return None
