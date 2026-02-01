"""
Date parser for natural language period references
Converts quarters, months, and period references to explicit date ranges
"""
import re
from datetime import datetime, date
from typing import Optional, Tuple


def parse_period(query: str) -> Optional[Tuple[str, str]]:
    """
    Parse period references in query and return (date_from, date_to) tuple.
    
    Supports:
    - Q1/Q2/Q3/Q4 2025
    - Quarter 1/2/3/4 2025
    - Kuartal 1/2/3/4 2025
    - Triwulan 1/2/3/4 2025
    
    Returns:
        Tuple of (date_from, date_to) in YYYY-MM-DD format, or None if no period found
    """
    query_lower = query.lower()
    
    # Extract year - try explicit year first, fallback to current year
    year_match = re.search(r'\b(20\d{2})\b', query)
    if year_match:
        year = year_match.group(1)
    else:
        year = str(datetime.now().year)
    
    # Quarter patterns (English)
    q1_patterns = [r'\bq1\b', r'quarter\s*1\b', r'first quarter\b']
    q2_patterns = [r'\bq2\b', r'quarter\s*2\b', r'second quarter\b']
    q3_patterns = [r'\bq3\b', r'quarter\s*3\b', r'third quarter\b']
    q4_patterns = [r'\bq4\b', r'quarter\s*4\b', r'fourth quarter\b', r'last quarter\b']
    
    # Indonesian quarter patterns
    q1_patterns.extend([r'kuartal\s*1\b', r'triwulan\s*1\b', r'kuartal\s*pertama\b'])
    q2_patterns.extend([r'kuartal\s*2\b', r'triwulan\s*2\b', r'kuartal\s*kedua\b'])
    q3_patterns.extend([r'kuartal\s*3\b', r'triwulan\s*3\b', r'kuartal\s*ketiga\b'])
    q4_patterns.extend([r'kuartal\s*4\b', r'triwulan\s*4\b', r'kuartal\s*keempat\b'])
    
    # Check Q1
    if any(re.search(pattern, query_lower) for pattern in q1_patterns):
        return (f'{year}-01-01', f'{year}-03-31')
    
    # Check Q2
    if any(re.search(pattern, query_lower) for pattern in q2_patterns):
        return (f'{year}-04-01', f'{year}-06-30')
    
    # Check Q3
    if any(re.search(pattern, query_lower) for pattern in q3_patterns):
        return (f'{year}-07-01', f'{year}-09-30')
    
    # Check Q4
    if any(re.search(pattern, query_lower) for pattern in q4_patterns):
        return (f'{year}-10-01', f'{year}-12-31')
    
    # Month name patterns (English)
    months_en = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    # Month name patterns (Indonesian)
    months_id = {
        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
        'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
        'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
    }
    
    # Check for specific month
    for month_name, month_num in {**months_en, **months_id}.items():
        if month_name in query_lower:
            # Get last day of month
            if month_num == 2:
                # February - check leap year
                year_int = int(year)
                is_leap = (year_int % 4 == 0 and year_int % 100 != 0) or (year_int % 400 == 0)
                last_day = 29 if is_leap else 28
            elif month_num in [4, 6, 9, 11]:
                last_day = 30
            else:
                last_day = 31
            
            return (f'{year}-{month_num:02d}-01', f'{year}-{month_num:02d}-{last_day}')
    
    return None


def enhance_query_with_dates(query: str) -> str:
    """
    Enhance query by appending explicit date range if period reference is found.
    
    Args:
        query: Original natural language query
    
    Returns:
        Enhanced query with explicit date range appended
    """
    period = parse_period(query)
    
    if period:
        date_from, date_to = period
        # Append explicit date range to query
        return f"{query} dari tanggal {date_from} sampai {date_to}"
    
    return query


# Test function
if __name__ == "__main__":
    test_queries = [
        "Berapa revenue Q4 2025?",
        "Invoice di quarter 3 2024",
        "Kuartal 2 2025 revenue",
        "Q1 penjualan",
        "Revenue bulan Oktober 2025",
        "Desember 2025 invoices"
    ]
    
    print("Date Parser Test Results:")
    print("=" * 70)
    
    for query in test_queries:
        result = parse_period(query)
        enhanced = enhance_query_with_dates(query)
        
        print(f"\nQuery: {query}")
        print(f"Parsed: {result}")
        print(f"Enhanced: {enhanced}")
