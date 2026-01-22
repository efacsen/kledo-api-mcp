# Phase 3: Tool Enhancement - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase clarifies tool selection by documenting overlaps and creating a disambiguation matrix. The scope is making the 23 existing tools easier to discover and choose correctly — NOT adding new tools or modifying existing tool implementations.

</domain>

<decisions>
## Implementation Decisions

### Matrix structure
- **Primary organization:** By business question (natural language queries like "What's my revenue?" map to recommended tools)
- **Format:** Markdown table with columns for Business Question, Recommended Tool, Alternative Tools, When to Use Alternative
- **Confidence indicators:** Include confidence levels (Definitive vs Context-dependent) to help AI agents know when they need more user input
- **Question variants:** Separate rows with cross-references (each phrasing gets its own row, with notes like "See also: revenue queries")

### Use case coverage
- **Question types:** Cover all four categories:
  - Reporting queries ("What's my revenue?", "Show sales trends")
  - Data lookup queries ("Show invoice #123", "Find customer X")
  - Analytical queries ("Who are my top customers?", "Compare Q1 vs Q2")
  - Status/health queries ("What's my cash balance?", "Any overdue invoices?")
- **Scale:** Essential coverage (10-15 questions) — high-impact scenarios that address 80% of use cases
- **Language:** Bilingual coverage (both English and Indonesian phrasings in the same matrix)
- **Parameter guidance:** Include parameter hints only (list required parameters without specific values, like "Needs: start_date, end_date")

### Tool grouping
- **Primary categorization:** By data entity (matches entity registry from Phase 1)
- **Entity ordering:** By business process flow (Contacts → Products → Invoices → Orders → Accounting)
- **Cross-entity tools:** Assign to primary entity (financial_sales_summary goes under Invoices, no separate "Reports" category)
- **Overlap indication:** Dedicated overlap section after each entity group ("Choosing between X and Y" subsections)

### Claude's Discretion
- Exact wording of business questions (as long as they represent common phrasings)
- Whether to split or merge similar question variants based on clarity
- Specific format of parameter hints
- Level of detail in overlap subsections

</decisions>

<specifics>
## Specific Ideas

- Matrix should make it obvious when tool choice is "Definitive" vs requires user context
- Indonesian terms should feel natural, not just direct translations (use actual business terminology from Kledo users)
- Business process flow: Contacts → Products → Invoices → Orders → Accounting reflects how users actually work with the system
- Parameter hints should be concise enough to fit in table cells without breaking layout

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope (documenting existing tools, not extending functionality).

</deferred>

---

*Phase: 03-tool-enhancement*
*Context gathered: 2026-01-22*
