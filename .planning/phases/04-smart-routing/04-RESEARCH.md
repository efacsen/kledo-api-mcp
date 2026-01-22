# Phase 4: Smart Routing - Research

**Researched:** 2026-01-22
**Domain:** Natural Language Query Routing, Synonym Mapping, Fuzzy Matching, Date Interpretation
**Confidence:** HIGH

## Summary

This research investigates the technical domain for implementing smart routing — enabling AI agents to discover the right tool from natural language business queries. The phase translates user intent (like "show me revenue", "piutang belum dibayar", or "last week's invoices") into specific tool selections with suggested parameters. The codebase already has 23 tools organized in 7 modules, comprehensive disambiguation documentation (Phase 3), and bilingual "Use for:" hints in llms.txt.

The key technical challenges are: (1) synonym dictionary mapping for bilingual business terms, (2) fuzzy matching for typo tolerance, (3) date/time interpretation distinguishing calendar-based vs rolling windows, and (4) relevance scoring for keyword-based tool ranking. The decision context from CONTEXT.md specifies returning all matching tools (not just best guess), supporting both English and Indonesian equally, and using simple keyword relevance without popularity bias.

**Primary recommendation:** Build a pure Python routing module using RapidFuzz for typo-tolerant matching, a hand-curated bilingual synonym dictionary (20-30 high-impact terms), custom date parsing extending the existing `parse_date_range()` helper, and keyword-based relevance scoring against tool metadata extracted from llms.txt "Use for:" hints.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| RapidFuzz | 3.14.x | Fuzzy string matching | MIT license, C++ performance, drop-in replacement for FuzzyWuzzy, pure Python fallback |
| Python stdlib (datetime, calendar) | 3.11+ | Calendar-aware date handling | Zero dependencies, ISO week support via isocalendar(), sufficient for "last week" vs "7 days" distinction |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dateparser | 1.2.x | Natural language date parsing | Only if need multi-language relative date support beyond custom implementation |
| isoweek | 1.3.x | ISO week number utilities | Only if calendar week calculations become complex |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| RapidFuzz | thefuzz (FuzzyWuzzy) | RapidFuzz 10-100x faster, MIT vs GPL license, active maintenance |
| Custom date parsing | dateparser | dateparser heavier (200 locales), overkill for 10-15 date patterns |
| Custom synonym dict | WordNet/NLTK | Domain-specific business terms not in general dictionaries; manual curation more accurate |
| BM25/TF-IDF | Simple keyword matching | 23 tools too small for statistical relevance; keyword overlap sufficient |

**Installation:**
```bash
pip install rapidfuzz>=3.14.0
# Optional: pip install dateparser>=1.2.0
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── routing/                    # NEW: Smart routing module
│   ├── __init__.py
│   ├── router.py              # Main routing logic: query -> tool suggestions
│   ├── synonyms.py            # Bilingual synonym dictionary
│   ├── patterns.py            # Pattern library for idiomatic expressions
│   ├── date_parser.py         # Extended date interpretation
│   └── scorer.py              # Relevance scoring logic
├── tools/                      # Existing tool implementations
└── utils/
    └── helpers.py             # Existing parse_date_range() to extend
```

### Pattern 1: Synonym Dictionary Structure
**What:** Hierarchical mapping from synonyms to canonical terms, then to tools.
**When to use:** Core routing lookup for business term normalization.
**Example:**
```python
# Source: CONTEXT.md decisions + Kledo business terminology

SYNONYM_MAP: dict[str, str] = {
    # English business terms -> canonical
    "revenue": "sales",
    "income": "sales",
    "earnings": "sales",
    "bill": "invoice",
    "bills": "invoice",
    "client": "customer",
    "clients": "customer",
    "supplier": "vendor",
    "suppliers": "vendor",

    # Indonesian business terms -> canonical
    "pendapatan": "sales",
    "penjualan": "sales",
    "faktur": "invoice",
    "tagihan": "invoice",
    "pelanggan": "customer",
    "pembeli": "customer",
    "pemasok": "vendor",
    "piutang": "receivable",
    "hutang": "payable",
    "saldo": "balance",
    "kas": "cash",
}

# Canonical term -> related tools
TERM_TO_TOOLS: dict[str, list[str]] = {
    "sales": ["financial_sales_summary", "invoice_list_sales", "order_list_sales"],
    "invoice": ["invoice_list_sales", "invoice_list_purchase", "invoice_get_detail", "invoice_get_totals"],
    "customer": ["contact_list", "contact_get_detail", "contact_get_transactions"],
    "vendor": ["contact_list", "invoice_list_purchase", "financial_purchase_summary"],
    "receivable": ["invoice_get_totals", "invoice_list_sales"],
    "payable": ["invoice_list_purchase", "financial_purchase_summary"],
    "balance": ["financial_bank_balances"],
    "cash": ["financial_bank_balances"],
}
```

### Pattern 2: Fuzzy Matching with RapidFuzz
**What:** Typo-tolerant lookup for user queries against synonym dictionary.
**When to use:** Before exact synonym lookup, to handle misspellings.
**Example:**
```python
# Source: RapidFuzz official documentation
from rapidfuzz import process, fuzz, utils

def fuzzy_lookup(query_term: str, dictionary: list[str], threshold: int = 80) -> str | None:
    """Find closest match for potentially misspelled term."""
    result = process.extractOne(
        query_term.lower(),
        dictionary,
        scorer=fuzz.WRatio,
        processor=utils.default_process,  # Lowercase + strip non-alphanumeric
        score_cutoff=threshold
    )
    if result:
        match, score, index = result
        return match
    return None

# Usage: "invoise" -> "invoice", "custmer" -> "customer", "tagiha" -> "tagihan"
```

### Pattern 3: Calendar-Aware Date Parsing
**What:** Distinguishes calendar boundaries ("last week") from rolling windows ("7 days ago").
**When to use:** Parameter suggestion for date-filtered tools.
**Example:**
```python
# Source: ISO 8601 week numbering + CONTEXT.md date handling decisions
from datetime import date, timedelta
from isoweek import Week  # Optional, can use isocalendar()

def parse_natural_date(phrase: str) -> tuple[date, date] | None:
    """Parse natural language date expressions."""
    today = date.today()
    phrase_lower = phrase.lower().strip()

    # Calendar-based: "last week" = previous ISO week (Mon-Sun)
    if phrase_lower in ("last week", "minggu lalu", "minggu kemarin"):
        last_week = Week.thisweek() - 1
        return last_week.monday(), last_week.sunday()

    # Calendar-based: "this month" = first day to today
    if phrase_lower in ("this month", "bulan ini"):
        return today.replace(day=1), today

    # Rolling window: "7 days ago", "tujuh hari kebelakang"
    if "7 days" in phrase_lower or "tujuh hari" in phrase_lower or "7 hari" in phrase_lower:
        return today - timedelta(days=7), today

    # Calendar-based: "Q1", "Q2", etc.
    if phrase_lower in ("q1", "kuartal 1"):
        year = today.year
        return date(year, 1, 1), date(year, 3, 31)

    # ... more patterns
    return None
```

### Pattern 4: Compound Expression Matching
**What:** Pattern library for multi-word idiomatic expressions with parameter hints.
**When to use:** Mapping phrases like "outstanding invoices" to tool + filter combo.
**Example:**
```python
# Source: CONTEXT.md pattern examples + llms.txt "Use for:" hints

PATTERNS: list[dict] = [
    {
        "patterns": ["outstanding invoices", "unpaid invoices", "faktur belum lunas"],
        "tool": "invoice_list_sales",
        "params": {"status_id": 2},  # Pending/unpaid status
        "confidence": "definitive"
    },
    {
        "patterns": ["who owes me money", "siapa yang hutang ke kita", "piutang belum dibayar"],
        "tool": "invoice_get_totals",
        "params": {},
        "alternative": "invoice_list_sales",
        "confidence": "context-dependent"  # Might want list vs summary
    },
    {
        "patterns": ["this month's revenue", "pendapatan bulan ini"],
        "tool": "financial_sales_summary",
        "params": "auto_date_this_month",  # Signal to auto-fill dates
        "confidence": "definitive"
    },
    {
        "patterns": ["customers who haven't paid", "pelanggan yang belum bayar"],
        "tool": "invoice_list_sales",
        "params": {"status_id": 2},  # Filter for unpaid
        "confidence": "definitive"
    },
]
```

### Pattern 5: Relevance Scoring
**What:** Keyword-based ranking with action verb awareness.
**When to use:** Ordering multiple matching tools when query is ambiguous.
**Example:**
```python
# Source: CONTEXT.md search ranking decisions

def score_tool(query_tokens: set[str], tool_name: str, tool_keywords: set[str]) -> float:
    """Score tool relevance based on keyword overlap and action context."""
    # Base score: count of matching keywords
    match_count = len(query_tokens & tool_keywords)

    # Action verb boost
    action_verbs = {
        "list": "_list",
        "show": "_list",
        "find": "_search",
        "search": "_search",
        "get": "_get",
        "detail": "_detail",
        "summary": "_summary",
        "total": "_totals",
    }

    for verb, suffix in action_verbs.items():
        if verb in query_tokens and suffix in tool_name:
            match_count += 0.5  # Boost for action match

    return match_count

# Tie-breaking: alphabetical (A-Z) as per CONTEXT.md
```

### Anti-Patterns to Avoid
- **Over-engineering NLP:** Don't use spaCy, BERT, or embeddings for 23 tools. Simple keyword matching + fuzzy lookup is sufficient.
- **Guessing single tool:** Always return multiple matching tools when query is ambiguous. Let user/agent pick.
- **Hard-coding English only:** Every pattern must have Indonesian equivalent from day one.
- **Ignoring existing work:** Build ON TOP of llms.txt and disambiguation.md, don't duplicate.
- **Complex scoring formulas:** Keep relevance scoring simple (keyword count + action boost). No ML needed at this scale.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Levenshtein distance | Custom edit distance algorithm | RapidFuzz | C++ optimized, handles Unicode, tested edge cases |
| ISO week number calculation | Manual week boundary math | `datetime.isocalendar()` or `isoweek` | ISO 8601 has edge cases (week 53, year boundary) |
| Tool metadata | Parse source code | Extract from llms.txt | Already has "Use for:" hints, bilingual, maintained |
| Synonym dictionary | Scrape thesaurus APIs | Hand-curated domain terms | Business Indonesian terms not in general dictionaries |

**Key insight:** The 23-tool scale means manual curation beats automation. The synonym dictionary (20-30 terms) is small enough to maintain by hand with high accuracy.

## Common Pitfalls

### Pitfall 1: Date Parsing Ambiguity
**What goes wrong:** "last week" interpreted as rolling 7 days instead of calendar week.
**Why it happens:** Different libraries and cultures have different defaults.
**How to avoid:** Explicitly define calendar vs rolling patterns in documentation. Test with edge cases (crossing year boundary, week 1 vs week 53).
**Warning signs:** User confusion when "last week" returns 7 days of data instead of Mon-Sun.

### Pitfall 2: Fuzzy Match False Positives
**What goes wrong:** "order" matches "border" with high score; "contact" matches "contract".
**Why it happens:** Levenshtein distance doesn't understand word meaning.
**How to avoid:** Set score threshold to 80+; use `fuzz.WRatio` (weighted ratio) not `fuzz.ratio`; require minimum 3-character terms; prefer exact match when available.
**Warning signs:** Unrelated tools appearing in suggestions.

### Pitfall 3: Indonesian Term Coverage Gaps
**What goes wrong:** Common Indonesian business terms not in synonym dictionary.
**Why it happens:** Initial list is developer-guessed, not user-validated.
**How to avoid:** Start with Kledo UI terminology; log unmatched queries for dictionary expansion; include colloquial terms ("hutang" not just formal "piutang").
**Warning signs:** Indonesian queries returning empty results while English equivalents work.

### Pitfall 4: Parameter Type Coercion
**What goes wrong:** Date suggestion returns string but tool expects datetime; ID suggestion returns string but tool expects int.
**Why it happens:** Natural language produces strings, but tool schemas have typed parameters.
**How to avoid:** Router should output parameter hints as strings with type annotations; actual coercion happens at tool invocation layer.
**Warning signs:** Type errors when calling suggested tool with suggested parameters.

### Pitfall 5: Vague Query Black Hole
**What goes wrong:** "show me data" returns every tool or random selection.
**Why it happens:** Query too vague, no meaningful keyword matches.
**How to avoid:** Detect vague queries (< 2 meaningful tokens after stopword removal); return clarifying question instead of arbitrary tools.
**Warning signs:** User confusion when unrelated tools suggested for generic queries.

### Pitfall 6: Action Verb Overweighting
**What goes wrong:** "show invoice list" returns only _list tools, missing invoice_get_detail that might be relevant.
**Why it happens:** Action verb boost too aggressive.
**How to avoid:** Action verb boost should be additive (0.5 points), not multiplicative; always include at least top 3 matches regardless of action match.
**Warning signs:** Narrower results than expected for specific action verbs.

## Code Examples

Verified patterns from official sources and CONTEXT.md decisions:

### RapidFuzz extractOne with Preprocessing
```python
# Source: RapidFuzz official documentation
from rapidfuzz import process, fuzz, utils

choices = ["invoice", "contact", "product", "order", "delivery", "financial"]

# Handles typos: "invoise" -> "invoice"
result = process.extractOne(
    "invoise",
    choices,
    scorer=fuzz.WRatio,
    processor=utils.default_process,
    score_cutoff=80
)
# Returns: ('invoice', 90.0, 0)
```

### ISO Week Calculation
```python
# Source: Python datetime documentation
from datetime import date, timedelta

def get_last_week_range() -> tuple[date, date]:
    """Get Monday-Sunday of the previous ISO week."""
    today = date.today()
    iso_cal = today.isocalendar()
    current_week_monday = today - timedelta(days=today.weekday())
    last_week_monday = current_week_monday - timedelta(weeks=1)
    last_week_sunday = last_week_monday + timedelta(days=6)
    return last_week_monday, last_week_sunday
```

### Keyword Extraction from Query
```python
# Source: Standard Python text processing
import re

STOPWORDS = {"show", "me", "the", "my", "a", "an", "get", "find", "what", "is", "are",
             "tampilkan", "saya", "apa", "berapa", "ini", "itu"}

def extract_keywords(query: str) -> set[str]:
    """Extract meaningful keywords from natural language query."""
    tokens = re.findall(r'\b\w+\b', query.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) >= 2}
```

### Tool Metadata Loading from llms.txt
```python
# Source: Existing llms.txt structure in codebase
import re

def load_tool_keywords() -> dict[str, set[str]]:
    """Load tool keywords from llms.txt 'Use for:' hints."""
    tool_keywords = {}

    with open("llms.txt") as f:
        content = f.read()

    # Pattern: [tool_name](...): Description. Use for: "kw1", "kw2", ...
    pattern = r'\[(\w+)\].*?Use for: ([^.]+)\.'
    for match in re.finditer(pattern, content):
        tool_name = match.group(1)
        use_for = match.group(2)
        keywords = set(re.findall(r'"([^"]+)"', use_for))
        tool_keywords[tool_name] = keywords

    return tool_keywords
```

### Routing Result Structure
```python
# Source: CONTEXT.md match detail level decision
from dataclasses import dataclass

@dataclass
class ToolSuggestion:
    """Single tool suggestion with context."""
    tool_name: str
    purpose: str           # Brief description
    key_params: list[str]  # Parameter names
    suggested_params: dict # Auto-filled values (e.g., date ranges)
    score: float           # Relevance score
    confidence: str        # "definitive" or "context-dependent"

@dataclass
class RoutingResult:
    """Result of routing a natural language query."""
    query: str
    matched_tools: list[ToolSuggestion]  # Ranked by relevance
    clarification_needed: str | None     # Question to ask if vague
    date_range: tuple[str, str] | None   # Auto-parsed dates
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single tool return | Multi-tool suggestions with ranking | CONTEXT.md decision | User/agent picks from options |
| English-only keywords | Bilingual synonym mapping | Kledo Indonesian context | Better local user experience |
| Fixed date parsing | Calendar vs rolling window distinction | CONTEXT.md decision | Accurate business reporting |
| Manual tool lookup | llms.txt "Use for:" hints | Phase 2 | Structured keyword source |
| Exact string match | Fuzzy matching with RapidFuzz | Modern NLP practice | Typo tolerance |

**Not applicable at this scale:**
- Vector embeddings for semantic search (overkill for 23 tools)
- LLM-based intent classification (simple pattern matching sufficient)
- Complex NLU pipelines (keyword + fuzzy matching adequate)

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal fuzzy match threshold**
   - What we know: RapidFuzz documentation suggests 80-90 for precision
   - What's unclear: Best threshold for Indonesian terms (might have different edit patterns)
   - Recommendation: Start at 80, tune based on false positive/negative rates

2. **Vague query response format**
   - What we know: CONTEXT.md says ask clarifying questions for vague queries
   - What's unclear: Exact wording of clarification questions; bilingual format
   - Recommendation: Return structured clarification object; let consumer format

3. **Pattern library initial size**
   - What we know: CONTEXT.md mentions patterns for "who owes me money", "outstanding invoices"
   - What's unclear: How many patterns are sufficient for MVP; diminishing returns point
   - Recommendation: Start with 10-15 high-impact patterns covering main workflows

4. **dateparser vs custom implementation**
   - What we know: dateparser supports Indonesian; custom code exists in helpers.py
   - What's unclear: Whether to extend custom or switch to dateparser
   - Recommendation: Extend existing `parse_date_range()` for consistency; add dateparser only if calendar week complexity warrants it

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/tools/*.py` — 23 tools, 7 modules reviewed
- Existing artifacts: `llms.txt`, `docs/tools/disambiguation.md`, `docs/tools/choosing.md` — Phase 2/3 work
- CONTEXT.md: User decisions on routing behavior, date handling, bilingual support
- [RapidFuzz PyPI](https://pypi.org/project/RapidFuzz/) — Version 3.14.3, installation, API examples
- [RapidFuzz Documentation](https://rapidfuzz.github.io/RapidFuzz/) — Scoring functions, preprocessing

### Secondary (MEDIUM confidence)
- [dateparser Documentation](https://dateparser.readthedocs.io/en/latest/) — Indonesian support confirmed, relative date patterns
- [Python isocalendar()](https://www.geeksforgeeks.org/python/isocalendar-method-of-datetime-class-in-python/) — ISO week number calculation
- [MCP Tool Discovery Patterns](https://portkey.ai/blog/mcp-tool-discovery-for-llm-agents/) — Tool routing in MCP context
- [isoweek Library](https://pypi.org/project/isoweek/) — ISO week utilities

### Tertiary (LOW confidence)
- [YAKE Keyword Extraction](https://github.com/LIAAD/yake) — Lightweight alternative if pattern matching insufficient
- [MCP-Zero Research](https://arxiv.org/html/2506.01056v3) — Semantic routing for large tool sets (not applicable at 23-tool scale)

## Metadata

**Confidence breakdown:**
- Standard stack (RapidFuzz): HIGH — MIT license, active maintenance, verified examples
- Synonym dictionary approach: HIGH — CONTEXT.md locked decision, matches existing llms.txt structure
- Date parsing patterns: MEDIUM — Calendar vs rolling distinction clear, edge cases need testing
- Indonesian terminology: MEDIUM — Based on Kledo context, may need user validation
- Relevance scoring: HIGH — Simple keyword matching sufficient per CONTEXT.md, no ML needed

**Research date:** 2026-01-22
**Valid until:** 2026-04-22 (90 days — routing patterns stable, main risk is Indonesian term coverage gaps)

---

*Phase: 04-smart-routing*
*Research completed: 2026-01-22*
