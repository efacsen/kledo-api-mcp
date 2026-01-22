"""
Keyword extraction and relevance scoring for smart routing.

Provides stopword filtering, action verb matching, and tool relevance scoring.
"""

import re
from pathlib import Path
from functools import lru_cache


# Stopwords: Common words to ignore in queries
# Includes both English and Indonesian
STOPWORDS: set[str] = {
    # English
    "show", "me", "the", "my", "a", "an", "get", "find", "what",
    "is", "are", "can", "you", "i", "want", "to", "see", "all",
    "please", "give", "how", "much", "many", "do", "does", "we", "have",
    "our", "us", "of", "in", "on", "for", "with", "from", "at", "by",
    # Indonesian
    "tampilkan", "saya", "apa", "berapa", "ini", "itu", "yang", "ke",
    "dari", "untuk", "di", "pada", "dengan", "oleh", "kita", "kami",
    "lihat", "cari", "mau", "ingin", "bisa", "tolong", "ada",
}


# Action verbs map to tool name suffixes for ranking boost
# Format: verb -> list of matching suffixes
ACTION_VERBS: dict[str, list[str]] = {
    # List/show actions -> _list tools
    "list": ["_list"],
    "show": ["_list"],
    "all": ["_list"],
    "daftar": ["_list"],  # Indonesian: list
    # Search/find actions -> _search tools
    "find": ["_search"],
    "search": ["_search"],
    "lookup": ["_search"],
    "cari": ["_search"],  # Indonesian: search
    # Detail/get actions -> _detail or _get tools
    "get": ["_detail", "_get"],
    "detail": ["_detail", "_get"],
    "info": ["_detail", "_get"],
    "details": ["_detail", "_get"],
    # Summary/report actions -> _summary or _totals tools
    "summary": ["_summary", "_totals"],
    "report": ["_summary", "_totals"],
    "total": ["_summary", "_totals"],
    "totals": ["_summary", "_totals"],
    "ringkasan": ["_summary", "_totals"],  # Indonesian: summary
    "laporan": ["_summary", "_totals"],  # Indonesian: report
}


def extract_keywords(query: str) -> set[str]:
    """
    Extract meaningful keywords from a query.

    Tokenizes the query, removes stopwords and short tokens.

    Args:
        query: Natural language query string

    Returns:
        Set of lowercase keywords, excluding stopwords and tokens < 2 chars
    """
    # Tokenize with word boundaries
    tokens = re.findall(r"\b\w+\b", query.lower())

    # Filter stopwords and short tokens
    keywords = {
        token for token in tokens
        if token not in STOPWORDS and len(token) >= 2
    }

    return keywords


def get_action_verb_suffixes(query_keywords: set[str]) -> list[str]:
    """
    Get tool name suffixes that match action verbs in the query.

    Args:
        query_keywords: Set of keywords from query

    Returns:
        List of tool name suffixes that should get a boost
    """
    suffixes = []
    for keyword in query_keywords:
        if keyword in ACTION_VERBS:
            suffixes.extend(ACTION_VERBS[keyword])
    return suffixes


def score_tool(
    query_keywords: set[str],
    tool_name: str,
    tool_keywords: set[str],
) -> float:
    """
    Score a tool's relevance to a query.

    Args:
        query_keywords: Keywords extracted from the query
        tool_name: Name of the tool being scored
        tool_keywords: Keywords associated with this tool (from llms.txt)

    Returns:
        Relevance score (higher = more relevant)
    """
    # Base score: count overlapping keywords
    overlap = query_keywords & tool_keywords
    base_score = float(len(overlap))

    # Also check if query keywords appear in tool name
    tool_name_lower = tool_name.lower()
    tool_name_parts = set(tool_name_lower.replace("_", " ").split())
    name_overlap = query_keywords & tool_name_parts
    base_score += len(name_overlap) * 0.5

    # Action verb boost: +0.5 if tool suffix matches action verb
    action_suffixes = get_action_verb_suffixes(query_keywords)
    for suffix in action_suffixes:
        if tool_name_lower.endswith(suffix):
            base_score += 0.5
            break  # Only one boost per tool

    return base_score


@lru_cache(maxsize=1)
def load_tool_keywords() -> dict[str, set[str]]:
    """
    Parse llms.txt to extract keywords per tool from "Use for:" hints.

    Returns:
        Dict mapping tool_name -> set of keywords from hints
    """
    tool_keywords: dict[str, set[str]] = {}

    # Find llms.txt in project root
    llms_path = Path(__file__).parent.parent.parent / "llms.txt"

    if not llms_path.exists():
        return tool_keywords

    content = llms_path.read_text()

    # Parse each tool line: - [tool_name](path): Description. Use for: "hints".
    # Pattern: starts with "- [", captures tool name, then finds "Use for:" section
    tool_pattern = re.compile(
        r"- \[([^\]]+)\]\([^)]+\): [^.]+\. Use for: \"([^\"]+)\""
    )

    for match in tool_pattern.finditer(content):
        tool_name = match.group(1)
        use_for_hints = match.group(2)

        # Extract keywords from hints
        keywords = extract_keywords(use_for_hints)

        # Also add tool name parts as keywords
        name_parts = set(tool_name.replace("_", " ").split())
        keywords.update(name_parts)

        tool_keywords[tool_name] = keywords

    return tool_keywords
