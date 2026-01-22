---
phase: 04-smart-routing
plan: 01
subsystem: routing
tags: [rapidfuzz, fuzzy-matching, date-parsing, bilingual, i18n]

requires:
  - phase: 03-tool-enhancement
    provides: Enhanced tools with entity awareness

provides:
  - Bilingual synonym dictionary (50 terms)
  - Extended date parser with calendar vs rolling distinction
  - Fuzzy matching utility for typo correction
  - Routing package structure

affects: [04-02, 04-03]

tech-stack:
  added: [rapidfuzz>=3.14.0]
  patterns:
    - "Canonical term normalization with self-mapping"
    - "ISO week calculation with datetime.isocalendar()"
    - "RapidFuzz WRatio scorer with 80 threshold"

key-files:
  created:
    - src/routing/__init__.py
    - src/routing/synonyms.py
    - src/routing/date_parser.py
    - src/routing/fuzzy.py
  modified:
    - requirements.txt

key-decisions:
  - "Canonical terms self-map in SYNONYM_MAP for fuzzy discoverability"
  - "80 score threshold + 3-char minimum for fuzzy matching precision"
  - "Calendar-based vs rolling window distinction for date parsing"

duration: 3 min
completed: 2026-01-22
---

# Phase 4 Plan 1: Smart Routing Foundation Summary

**Bilingual synonym dictionary (50 terms), extended date parser with calendar/rolling distinction, and RapidFuzz-powered typo correction**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-22T11:44:46Z
- **Completed:** 2026-01-22T11:48:22Z
- **Tasks:** 4
- **Files modified:** 5

## Accomplishments

- Created routing package structure with proper exports
- Built bilingual synonym dictionary with 50 terms (12 canonical + 38 alternates)
- Implemented date parser supporting 15+ patterns (calendar and rolling)
- Added fuzzy matching with RapidFuzz for typo correction

## Task Commits

Each task was committed atomically:

1. **Task 1: Add RapidFuzz dependency + routing package structure** - `14c029b` (chore)
2. **Task 2: Create bilingual synonym dictionary** - `2180f36` (feat)
3. **Task 3: Create extended date parser** - `87b55e5` (feat)
4. **Task 4: Create fuzzy matching utility** - `572608a` (feat)

## Files Created/Modified

- `requirements.txt` - Added rapidfuzz>=3.14.0 dependency
- `src/routing/__init__.py` - Package exports (SYNONYM_MAP, TERM_TO_TOOLS, normalize_term, parse_natural_date, fuzzy_lookup)
- `src/routing/synonyms.py` - Bilingual synonym dictionary with 50 terms
- `src/routing/date_parser.py` - Extended date parser (calendar + rolling windows)
- `src/routing/fuzzy.py` - Fuzzy matching utility with RapidFuzz

## Decisions Made

1. **Canonical terms self-map in SYNONYM_MAP** - Added canonical terms (sales, invoice, customer, etc.) as self-mapping entries so fuzzy matching can discover them. Without this, "invoise" couldn't match "invoice" since it wasn't in the dictionary keys.

2. **80 score threshold + 3-char minimum** - Balances typo correction precision with avoiding false positives. 80 threshold catches reasonable typos while rejecting unrelated terms.

3. **Calendar-based vs rolling window distinction** - "Last week" returns previous ISO week (Mon-Sun), not rolling 7 days. This matches business reporting expectations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added canonical terms to SYNONYM_MAP**
- **Found during:** Task 4 (fuzzy matching verification)
- **Issue:** "invoise" couldn't fuzzy-match to "invoice" because canonical terms weren't in SYNONYM_MAP keys
- **Fix:** Added 12 canonical terms as self-mappings (invoice->invoice, customer->customer, etc.)
- **Files modified:** src/routing/synonyms.py
- **Verification:** fuzzy_lookup("invoise") now returns "invoice" with 85.7% score
- **Committed in:** 572608a (Task 4 commit)

---

**Total deviations:** 1 auto-fixed (blocking issue)
**Impact on plan:** Essential for fuzzy matching to work correctly. No scope creep.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Routing foundation components ready for main router composition
- Ready for 04-02-PLAN.md (intent detection and routing logic)
- All exports available via `from src.routing import ...`

---
*Phase: 04-smart-routing*
*Completed: 2026-01-22*
