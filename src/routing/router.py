"""
Main routing logic for smart tool discovery.

Composes synonyms, patterns, date parsing, and scoring to resolve
natural language queries to tool suggestions.
"""

import re
from dataclasses import dataclass, field
from datetime import date

from src.routing.patterns import match_pattern
from src.routing.synonyms import normalize_term, TERM_TO_TOOLS
from src.routing.date_parser import parse_natural_date
from src.routing.fuzzy import fuzzy_lookup
from src.routing.scorer import (
    extract_keywords,
    score_tool,
    load_tool_keywords,
    STOPWORDS,
)


@dataclass
class ToolSuggestion:
    """A suggested tool with relevance details."""
    tool_name: str
    purpose: str
    key_params: list[str]
    suggested_params: dict
    score: float
    confidence: str  # "definitive" or "context-dependent"


@dataclass
class RoutingResult:
    """Result of routing a natural language query."""
    query: str
    matched_tools: list[ToolSuggestion] = field(default_factory=list)
    clarification_needed: str | None = None
    date_range: tuple[str, str] | None = None


# Tool metadata from llms.txt (purpose and key params)
# Maps tool_name -> (purpose, key_params)
TOOL_METADATA: dict[str, tuple[str, list[str]]] = {
    # Invoice Tools
    "invoice_list_sales": (
        "List sales invoices",
        ["search", "contact_id", "status_id", "date_from", "date_to"],
    ),
    "invoice_get_detail": (
        "Get invoice details with line items",
        ["invoice_id"],
    ),
    "invoice_get_totals": (
        "Get invoice summary totals",
        ["date_from", "date_to"],
    ),
    "invoice_list_purchase": (
        "List purchase invoices (vendor bills)",
        ["search", "contact_id", "status_id", "date_from", "date_to"],
    ),
    # Contact Tools
    "contact_list": (
        "List customers and vendors",
        ["search", "type_id"],
    ),
    "contact_get_detail": (
        "Get contact details",
        ["contact_id"],
    ),
    "contact_get_transactions": (
        "Get contact transaction history",
        ["contact_id"],
    ),
    # Product Tools
    "product_list": (
        "List products with prices",
        ["search", "include_inventory"],
    ),
    "product_get_detail": (
        "Get product details",
        ["product_id"],
    ),
    "product_search_by_sku": (
        "Find product by SKU",
        ["sku"],
    ),
    # Order Tools
    "order_list_sales": (
        "List sales orders",
        ["search", "contact_id", "status_id", "date_from", "date_to"],
    ),
    "order_get_detail": (
        "Get order details",
        ["order_id"],
    ),
    "order_list_purchase": (
        "List purchase orders",
        ["search", "contact_id", "date_from", "date_to"],
    ),
    # Delivery Tools
    "delivery_list": (
        "List deliveries",
        ["search", "date_from", "date_to", "status_id"],
    ),
    "delivery_get_detail": (
        "Get delivery details",
        ["delivery_id"],
    ),
    "delivery_get_pending": (
        "Get pending deliveries",
        [],
    ),
    # Financial Tools
    "financial_activity_team_report": (
        "Team activity report",
        ["date_from", "date_to"],
    ),
    "financial_sales_summary": (
        "Sales by customer",
        ["date_from", "date_to", "contact_id"],
    ),
    "financial_purchase_summary": (
        "Purchases by vendor",
        ["date_from", "date_to", "contact_id"],
    ),
    "financial_bank_balances": (
        "Bank account balances",
        [],
    ),
    # System Tools
    "utility_clear_cache": (
        "Clear cached data",
        [],
    ),
    "utility_get_cache_stats": (
        "Cache performance metrics",
        [],
    ),
    "utility_test_connection": (
        "Test API connection",
        [],
    ),
}


# Date expression patterns to detect in queries
DATE_PATTERNS = [
    # Calendar-based
    r"\blast week\b",
    r"\bminggu lalu\b",
    r"\bminggu kemarin\b",
    r"\bthis week\b",
    r"\bminggu ini\b",
    r"\bthis month\b",
    r"\bbulan ini\b",
    r"\blast month\b",
    r"\bbulan lalu\b",
    r"\bbulan kemarin\b",
    r"\bthis year\b",
    r"\btahun ini\b",
    r"\blast year\b",
    r"\btahun lalu\b",
    r"\btahun kemarin\b",
    # Quarters
    r"\bq[1-4]\b",
    r"\bkuartal [1-4]\b",
    r"\bquarter [1-4]\b",
    # Rolling windows
    r"\b\d+\s*(?:days?|hari)\b",
    r"\b(?:seven|fourteen|thirty|sixty|ninety)\s*days\b",
    r"\b(?:tujuh|sepuluh|empat belas|lima belas|dua puluh|tiga puluh|enam puluh|sembilan puluh)\s*hari\b",
    # Specific days
    r"\byesterday\b",
    r"\bkemarin\b",
    r"\btoday\b",
    r"\bhari ini\b",
]


def _extract_date_expression(query: str) -> str | None:
    """Extract date expression from query if present."""
    query_lower = query.lower()
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            return match.group(0)
    return None


def _resolve_auto_date_params(params: str | dict, date_range: tuple[date, date] | None) -> dict:
    """Resolve auto_date_* params to actual date values."""
    if isinstance(params, dict):
        return params

    if not date_range:
        return {}

    if params == "auto_date_this_month":
        return {
            "date_from": date_range[0].isoformat(),
            "date_to": date_range[1].isoformat(),
        }

    return {}


def _create_suggestion_from_pattern(
    pattern_match: dict,
    date_range: tuple[date, date] | None,
) -> list[ToolSuggestion]:
    """Create tool suggestions from a pattern match."""
    suggestions = []

    tool_name = pattern_match["tool"]
    params = _resolve_auto_date_params(pattern_match.get("params", {}), date_range)
    confidence = pattern_match.get("confidence", "definitive")

    # Get tool metadata
    purpose, key_params = TOOL_METADATA.get(tool_name, ("", []))

    suggestions.append(ToolSuggestion(
        tool_name=tool_name,
        purpose=purpose,
        key_params=key_params,
        suggested_params=params,
        score=10.0,  # High score for pattern matches
        confidence=confidence,
    ))

    # Add alternative tool if exists
    alternative = pattern_match.get("alternative")
    if alternative:
        alt_purpose, alt_params = TOOL_METADATA.get(alternative, ("", []))
        suggestions.append(ToolSuggestion(
            tool_name=alternative,
            purpose=alt_purpose,
            key_params=alt_params,
            suggested_params=params,
            score=9.0,  # Slightly lower for alternative
            confidence="context-dependent",
        ))

    return suggestions


def _normalize_keywords(keywords: set[str]) -> set[str]:
    """Normalize keywords using synonyms and fuzzy matching."""
    normalized = set()

    for keyword in keywords:
        # First try direct synonym normalization
        canonical = normalize_term(keyword)
        if canonical != keyword:
            normalized.add(canonical)
            continue

        # Try fuzzy matching for typos
        fuzzy_match = fuzzy_lookup(keyword)
        if fuzzy_match:
            # Fuzzy matched to a synonym, normalize it
            canonical = normalize_term(fuzzy_match)
            normalized.add(canonical)
        else:
            # Keep original keyword
            normalized.add(keyword)

    return normalized


def _get_tools_for_terms(normalized_keywords: set[str]) -> set[str]:
    """Get candidate tools based on normalized keywords."""
    tools = set()
    for keyword in normalized_keywords:
        if keyword in TERM_TO_TOOLS:
            tools.update(TERM_TO_TOOLS[keyword])
    return tools


def route_query(query: str) -> RoutingResult:
    """
    Route a natural language query to tool suggestions.

    Algorithm:
    1. Check for idiomatic pattern match first
    2. Extract keywords and check for date expressions
    3. Normalize keywords via synonyms and fuzzy matching
    4. If too few keywords, return clarification request
    5. Score all tools and return top suggestions

    Args:
        query: Natural language query string

    Returns:
        RoutingResult with matched tools and optional clarification/date range
    """
    result = RoutingResult(query=query)

    # Step 1: Check for idiomatic pattern match first
    pattern_match = match_pattern(query)

    # Step 2: Extract date expression if present
    date_expr = _extract_date_expression(query)
    date_range: tuple[date, date] | None = None
    if date_expr:
        parsed = parse_natural_date(date_expr)
        if parsed:
            date_range = parsed
            result.date_range = (parsed[0].isoformat(), parsed[1].isoformat())

    # If pattern matched, use it as primary result
    if pattern_match:
        suggestions = _create_suggestion_from_pattern(pattern_match, date_range)
        result.matched_tools = suggestions
        return result

    # Step 3: Extract keywords
    keywords = extract_keywords(query)

    # Step 4: Normalize keywords
    normalized = _normalize_keywords(keywords)

    # Step 5: Get candidate tools from normalized keywords
    candidate_tools = _get_tools_for_terms(normalized)

    # If no candidate tools found, check if query is too vague
    # "show invoices" -> has tools -> proceed
    # "show me data" -> no tools -> request clarification
    if not candidate_tools and len(normalized) < 2:
        result.clarification_needed = (
            "What would you like to know? For example: invoices, customers, "
            "sales, products..."
        )
        return result

    # Step 6: Score all tools
    tool_keywords = load_tool_keywords()

    scored_suggestions: list[ToolSuggestion] = []

    # Score candidate tools first
    for tool_name in candidate_tools:
        if tool_name not in TOOL_METADATA:
            continue

        tool_kw = tool_keywords.get(tool_name, set())
        score = score_tool(normalized, tool_name, tool_kw)

        if score > 0:
            purpose, key_params = TOOL_METADATA[tool_name]
            scored_suggestions.append(ToolSuggestion(
                tool_name=tool_name,
                purpose=purpose,
                key_params=key_params,
                suggested_params={},
                score=score,
                confidence="context-dependent",
            ))

    # Also score other tools that might match
    for tool_name in TOOL_METADATA:
        if tool_name in candidate_tools:
            continue  # Already scored

        tool_kw = tool_keywords.get(tool_name, set())
        score = score_tool(normalized, tool_name, tool_kw)

        if score > 0:
            purpose, key_params = TOOL_METADATA[tool_name]
            scored_suggestions.append(ToolSuggestion(
                tool_name=tool_name,
                purpose=purpose,
                key_params=key_params,
                suggested_params={},
                score=score,
                confidence="context-dependent",
            ))

    # Sort by score descending, then alphabetically for ties
    scored_suggestions.sort(key=lambda s: (-s.score, s.tool_name))

    # Return top 5 suggestions
    result.matched_tools = scored_suggestions[:5]

    # Add date params to suggestions if date range was extracted
    if date_range:
        for suggestion in result.matched_tools:
            if "date_from" in suggestion.key_params:
                suggestion.suggested_params = {
                    "date_from": date_range[0].isoformat(),
                    "date_to": date_range[1].isoformat(),
                }

    return result
