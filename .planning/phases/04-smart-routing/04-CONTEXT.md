# Phase 4: Smart Routing - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Enable AI agents to discover the right tool from natural language business queries. This phase translates user intent (like "show me revenue", "piutang belum dibayar", or "last week's invoices") into specific tool selections with suggested parameters. Uses synonym dictionaries, pattern recognition, and contextual understanding to bridge conversational queries and API tools.

**Scope:** Natural language query → tool discovery + parameter suggestions. NOT about executing tools, modifying the API, or adding new business capabilities. Makes existing tools discoverable through conversational queries.

</domain>

<decisions>
## Implementation Decisions

### Query Interpretation
- **Ambiguous queries:** Return all matching tools, not just best guess
  - Example: "show invoices" returns invoice_list, invoice_search, sales_summary
  - Let user/agent pick from options rather than making assumptions
- **Match detail level:** Tool name + purpose + key parameters
  - Example: "invoice_list - Get all invoices. Params: status, date_from, date_to"
  - Enough context for informed choice without overwhelming with full docs
- **Pattern recognition:** YES - build pattern library for common queries
  - "who owes me money" → accounts receivable tools
  - "outstanding invoices" → invoice_list with status=unpaid hint
  - Handles idiomatic expressions and business queries
- **Vague queries:** Ask clarifying questions, don't guess
  - "show me data" → prompt "What type of data? Invoices, contacts, products, or something else?"
  - Interactive disambiguation rather than returning arbitrary suggestions

### Synonym Coverage
- **Language priority:** Both English and Indonesian equally
  - No preference hierarchy, all terms treated the same
  - Optimized for bilingual Kledo user context
- **Coverage scope:** Core business terms only (20-30 key synonyms)
  - Focus: invoice/bill/tagihan, customer/client/pelanggan, revenue/sales/pendapatan
  - Maintainable, high-impact terms rather than exhaustive dictionary
- **Typo handling:** YES - fuzzy matching for misspellings
  - Allow close matches: invoise → invoice, custmer → customer, tagihan → tagiha
  - More forgiving for conversational queries
- **Compound terms:** YES - with parameter hints
  - "outstanding invoices" → invoice_list + status=unpaid hint
  - "this month's revenue" → financial_sales_summary + date range hint
  - Maps multi-word phrases to tool + suggested params

### Search Ranking
- **Primary ranking factor:** Keyword relevance
  - Tools with more query keywords rank higher
  - "invoice status" ranks invoice_list above contact_list
- **Popularity consideration:** NO - relevance only
  - Pure keyword matching, treat all tools equally
  - Don't bias toward frequently used tools
- **Tie-breaking:** Alphabetical order (A-Z)
  - Predictable, simple when multiple tools have identical scores
  - No artificial preference or complex sub-ranking
- **Context awareness:** YES - adapt ranking based on query action
  - "list invoices" ranks _list tools higher
  - "find invoice" ranks _search tools higher
  - "invoice summary" ranks _summary tools higher
  - Action verbs influence tool type preference

### Parameter Suggestion
- **Implicit parameters:** Auto-fill with calculated values
  - "this month's invoices" → date_from=2026-01-01, date_to=2026-01-31
  - Pre-calculate based on current date, don't prompt
- **Missing required params:** Suggest sensible defaults
  - "invoice_list (showing all statuses by default)"
  - Offer tool with defaults rather than blocking or prompting
- **Domain awareness:** YES - use business logic for suggestions
  - "revenue" → financial_sales_summary with amount aggregation
  - Understands business intent, not just keyword matching
- **Date/time interpretation:** Calendar-aware with rolling fallback
  - **"last week"** → previous calendar week by week number
    - If today is Week 3, query Week 2 (Mon-Sun of that week)
  - **"7 days ago" / "tujuh hari kebelakang"** → rolling 7 days from today
  - **"Q1" / "FY"** → business calendar (Q1 = Jan-Mar)
  - **"this month"** → current calendar month (Jan 1 to today if mid-month)
  - Distinction: formal terms use calendar boundaries, specific durations use rolling windows

### Claude's Discretion
- Exact fuzzy matching algorithm (Levenshtein distance threshold, etc.)
- Relevance scoring formula details
- Pattern library initial content (can expand based on real usage)
- Error message wording for edge cases
- Implementation of query parsing (regex, NLP, etc.)

</decisions>

<specifics>
## Specific Ideas

- **Date handling is critical:** User emphasized the difference between calendar-based ("last week" = previous week number) vs. rolling window ("7 days ago" = literal 7-day span). System must recognize this distinction in Indonesian and English.

- **Bilingual context:** Kledo users switch between English and Indonesian naturally. Synonym mapping should work seamlessly in both directions without language preference.

- **Pattern examples to support:**
  - "who owes me money" → receivables/piutang
  - "outstanding invoices" → unpaid status filter
  - "this month's sales" → date range + sales tools
  - "pelanggan yang belum bayar" → customer list + unpaid filter

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope (query routing and parameter suggestion, not execution or API modification).

</deferred>

---

*Phase: 04-smart-routing*
*Context gathered: 2026-01-22*
