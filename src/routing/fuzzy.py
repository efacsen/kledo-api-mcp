"""
Fuzzy matching utility for typo-tolerant term lookup.

Uses RapidFuzz for high-performance fuzzy string matching
against the synonym dictionary.
"""

from rapidfuzz import fuzz, process, utils

from src.routing.synonyms import SYNONYM_MAP


def fuzzy_lookup(
    term: str,
    candidates: list[str] | None = None,
    threshold: int = 80,
) -> str | None:
    """
    Find the closest matching term using fuzzy matching.

    Args:
        term: The input term (possibly with typos)
        candidates: List of terms to match against.
                   Defaults to SYNONYM_MAP keys if None.
        threshold: Minimum score (0-100) for a match. Default 80.

    Returns:
        The matched term if found with score >= threshold, None otherwise.
        Returns None for terms shorter than 3 characters to avoid false positives.
    """
    # Minimum 3 characters to avoid false positives
    if len(term) < 3:
        return None

    # Use SYNONYM_MAP keys as default candidates
    if candidates is None:
        candidates = list(SYNONYM_MAP.keys())

    if not candidates:
        return None

    # Use extractOne with WRatio scorer for better partial matching
    result = process.extractOne(
        term,
        candidates,
        scorer=fuzz.WRatio,
        processor=utils.default_process,
        score_cutoff=threshold,
    )

    if result is None:
        return None

    matched_term, score, index = result
    return matched_term
