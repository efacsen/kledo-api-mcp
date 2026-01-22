"""
Smart routing components for natural language query processing.

This package provides the complete smart routing module:
- router: Main routing logic with route_query() entry point
- patterns: Pattern library for idiomatic expressions
- synonyms: Bilingual synonym dictionary (English + Indonesian)
- date_parser: Extended natural language date parsing
- fuzzy: Typo-tolerant term matching
- scorer: Keyword extraction and relevance scoring
"""

from src.routing.router import route_query, ToolSuggestion, RoutingResult
from src.routing.synonyms import SYNONYM_MAP, TERM_TO_TOOLS, normalize_term
from src.routing.date_parser import parse_natural_date
from src.routing.fuzzy import fuzzy_lookup
from src.routing.patterns import match_pattern, PATTERNS
from src.routing.scorer import extract_keywords, score_tool

__all__ = [
    # Router (main entry point)
    "route_query",
    "ToolSuggestion",
    "RoutingResult",
    # Synonyms
    "normalize_term",
    "SYNONYM_MAP",
    "TERM_TO_TOOLS",
    # Date parsing
    "parse_natural_date",
    # Fuzzy matching
    "fuzzy_lookup",
    # Patterns
    "match_pattern",
    "PATTERNS",
    # Scoring
    "extract_keywords",
    "score_tool",
]
