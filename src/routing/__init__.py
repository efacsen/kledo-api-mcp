"""
Smart routing components for natural language query processing.

This package provides foundation components for smart routing:
- synonyms: Bilingual synonym dictionary (English + Indonesian)
- date_parser: Extended natural language date parsing
- fuzzy: Typo-tolerant term matching
"""

from src.routing.synonyms import SYNONYM_MAP, TERM_TO_TOOLS, normalize_term
from src.routing.date_parser import parse_natural_date

__all__ = ["SYNONYM_MAP", "TERM_TO_TOOLS", "normalize_term", "parse_natural_date"]
