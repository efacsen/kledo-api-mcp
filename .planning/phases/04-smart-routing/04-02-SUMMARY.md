---
phase: 04-smart-routing
plan: 02
subsystem: routing
tags: [natural-language, query-routing, patterns, scoring, bilingual]

requires:
  - phase: 04-01
    provides: Synonym dictionary, date parser, fuzzy matching

provides:
  - Pattern library for idiomatic expressions (10 bilingual patterns)
  - Keyword extraction with stopword filtering
  - Relevance scoring with action verb boost
  - Main router composing all routing components

affects: [04-03]

tech-stack:
  added: []
  patterns:
    - "Pattern matching for idiomatic business phrases"
    - "Keyword normalization for consistent tool matching"
    - "Action verb suffix matching for ranking"

key-files:
  created:
    - src/routing/patterns.py
    - src/routing/scorer.py
    - src/routing/router.py
  modified:
    - src/routing/__init__.py
    - src/routing/synonyms.py

key-decisions:
  - "Pattern matching takes precedence over keyword scoring"
  - "Vague queries request clarification instead of guessing"
  - "Tool keywords normalized to canonical forms for matching"

duration: 6 min
completed: 2026-01-22
---

# Phase 4 Plan 2: Smart Routing Logic Summary

**Pattern library for idiomatic expressions, keyword scoring with action verb boost, and main router composing synonyms/patterns/dates/fuzzy for tool discovery**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-22T11:51:48Z
- **Completed:** 2026-01-22T11:57:47Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Created pattern library with 10 bilingual idiomatic expressions
- Built keyword extraction with English + Indonesian stopword filtering
- Implemented relevance scoring with action verb suffix boost
- Composed main router integrating all routing components

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pattern library for idiomatic expressions** - `3b5c96e` (feat)
2. **Task 2: Create keyword extraction and relevance scoring** - `833d6e4` (feat)
3. **Task 3: Create main router with multi-tool suggestions** - `928e3b5` (feat)

## Files Created/Modified

- `src/routing/patterns.py` - Pattern library with 10 idiomatic expressions (EN + ID)
- `src/routing/scorer.py` - Keyword extraction, stopwords, action verb matching, scoring
- `src/routing/router.py` - Main router with route_query(), ToolSuggestion, RoutingResult
- `src/routing/__init__.py` - Updated exports for complete routing module
- `src/routing/synonyms.py` - Added plural forms (invoices, customers, vendors, etc.)

## Decisions Made

1. **Pattern matching takes precedence** - Idiomatic expressions like "outstanding invoices" get immediate tool match with high score (10.0) before any keyword scoring.

2. **Vague queries request clarification** - Queries with no domain keywords ("show me data") return clarification prompt instead of arbitrary tools. But single domain terms ("show invoices") return relevant tools.

3. **Tool keywords normalized** - Keywords from llms.txt "Use for:" hints are normalized to canonical forms (customers -> customer) for consistent matching with query keywords.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added plural forms to SYNONYM_MAP**
- **Found during:** Task 3 (router verification)
- **Issue:** "show invoices" returned 0 tools because "invoices" (plural) wasn't in SYNONYM_MAP
- **Fix:** Added plural forms: invoices, customers, vendors, products, deliveries, balances, shipments
- **Files modified:** src/routing/synonyms.py
- **Verification:** "show invoices" now returns 4 invoice tools
- **Committed in:** 928e3b5 (Task 3 commit)

**2. [Rule 3 - Blocking] Normalized tool keywords from llms.txt**
- **Found during:** Task 3 (router verification)
- **Issue:** "show customers" missing contact_list because tool had "customers" but query normalized to "customer"
- **Fix:** Normalize keywords in load_tool_keywords() using normalize_term()
- **Files modified:** src/routing/scorer.py
- **Verification:** "show customers" now includes contact_list
- **Committed in:** 928e3b5 (Task 3 commit)

**3. [Rule 3 - Blocking] Adjusted vague query threshold**
- **Found during:** Task 3 (router verification)
- **Issue:** Single domain keyword like "invoices" was triggering clarification (< 2 keywords)
- **Fix:** Changed logic to check if candidate tools exist rather than raw keyword count
- **Files modified:** src/routing/router.py
- **Verification:** "show invoices" returns tools, "show me data" requests clarification
- **Committed in:** 928e3b5 (Task 3 commit)

---

**Total deviations:** 3 auto-fixed (all blocking issues)
**Impact on plan:** All fixes necessary for correct routing behavior. No scope creep.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Complete routing module ready for integration
- route_query() provides main entry point
- Ready for 04-03-PLAN.md (API integration or testing)
- All exports available via `from src.routing import ...`

---
*Phase: 04-smart-routing*
*Completed: 2026-01-22*
