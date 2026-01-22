# Phase 3: Tool Enhancement - Research

**Researched:** 2026-01-22
**Domain:** Tool Disambiguation Matrix Design, MCP Tool Selection Patterns, Business Query Mapping
**Confidence:** HIGH

## Summary

This research investigates the technical domain for creating a tool disambiguation matrix and overlap documentation for the existing 23 MCP tools. The phase scope is clarifying tool selection for AI agents and users — NOT adding new tools or modifying implementations. The codebase already has complete tool implementations (7 modules, 23 tools) and Phase 2 documentation (llms.txt with "Use for:" hints, MkDocs site).

The key challenge is distinguishing between tools that serve overlapping purposes (e.g., `invoice_list_sales` vs `financial_sales_summary` — both relate to "revenue" queries but serve different needs). The disambiguation matrix addresses this by mapping business questions to recommended tools with confidence indicators.

**Primary recommendation:** Create a Markdown-based tool disambiguation matrix organized by business question categories (Reporting, Lookup, Analysis, Status/Health), with dedicated "Choosing Between" subsections for overlapping tools. Use a table format with columns for Business Question (bilingual), Recommended Tool, Alternative Tools, When to Use Alternative, and Confidence Level (Definitive vs Context-dependent).

## Standard Stack

The established patterns/tools for this domain:

### Core Artifacts
| Artifact | Format | Purpose | Why Standard |
|----------|--------|---------|--------------|
| Disambiguation Matrix | Markdown table | Map questions to tools | Readable by AI agents, humans, and CI validation |
| Overlap Documentation | Markdown prose | Explain similar tool differences | Natural language explanations for nuanced decisions |
| llms.txt update | Markdown list | Enhanced discovery hints | Already exists, can be augmented with disambiguation links |

### Supporting Patterns
| Pattern | Source | Purpose | When to Use |
|---------|--------|---------|-------------|
| Decision Tree | API documentation pattern | Guide complex choices | When multiple criteria determine tool selection |
| Entity-based grouping | Phase 1 registry | Organize by data domain | Match existing codebase organization |
| Bilingual phrasing | Indonesian business terminology | Support actual user queries | Kledo is Indonesian software |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Markdown tables | JSON/YAML lookup | Markdown more readable by AI, easier to maintain manually |
| Single matrix file | Distributed per-domain | Single file provides unified view, easier cross-referencing |
| Question-first organization | Tool-first organization | Question-first matches how users think, more intuitive discovery |

**No additional dependencies required.** This phase is documentation-only.

## Architecture Patterns

### Recommended File Structure
```
docs/
├── tools/
│   ├── index.md                # Existing tool catalog (from Phase 2)
│   ├── disambiguation.md       # NEW: Main disambiguation matrix
│   └── overlaps/               # NEW: Detailed overlap explanations
│       ├── invoice-vs-sales-summary.md
│       ├── contact-vs-customer-tools.md
│       └── order-vs-invoice-tools.md
llms.txt                        # Existing (augment with disambiguation references)
```

### Pattern 1: Business Question Matrix Structure
**What:** Table mapping natural language questions to tool recommendations.
**When to use:** Primary disambiguation artifact — the main tool selection guide.
**Example:**
```markdown
## Revenue & Sales Questions

| Business Question | ID: Pertanyaan Bisnis | Recommended Tool | Alternatives | When to Use Alternative | Confidence |
|-------------------|----------------------|------------------|--------------|------------------------|------------|
| What's my revenue this month? | Berapa pendapatan bulan ini? | `financial_sales_summary` | `invoice_list_sales` | Need invoice-level detail, not just totals | Definitive |
| Show me sales invoices | Tampilkan faktur penjualan | `invoice_list_sales` | - | - | Definitive |
| Who are my top customers? | Siapa pelanggan terbesar? | `financial_sales_summary` | `contact_list` + `invoice_list_sales` | Need full contact details beyond revenue | Definitive |
| How much does customer X owe? | Berapa hutang pelanggan X? | `contact_get_detail` | `invoice_list_sales` | Need itemized invoice list, not summary | Context-dependent |

### See Also
- [Invoice vs Sales Summary: Which to Use?](overlaps/invoice-vs-sales-summary.md)
```

### Pattern 2: Overlap Explanation Structure
**What:** Dedicated page explaining when to choose between similar tools.
**When to use:** For tool pairs that frequently cause selection confusion.
**Example:**
```markdown
# Choosing Between: invoice_list_sales vs financial_sales_summary

## Quick Decision

| If you need... | Use |
|----------------|-----|
| Individual invoice records | `invoice_list_sales` |
| Revenue totals by customer | `financial_sales_summary` |
| Unpaid/overdue amounts | `invoice_list_sales` (has status filter) |
| Top customer ranking | `financial_sales_summary` |
| Invoice line items | `invoice_get_detail` (after getting ID from list) |

## Detailed Comparison

| Aspect | invoice_list_sales | financial_sales_summary |
|--------|-------------------|------------------------|
| **Returns** | List of invoice records | Aggregated totals by contact |
| **Granularity** | Invoice-level | Contact-level (grouped) |
| **Best for** | "Show invoices for customer X" | "Who bought the most?" |
| **Parameters** | search, contact_id, status_id, date_from, date_to | date_from, date_to, contact_id |
| **Output includes** | Invoice number, status, amounts, dates | Contact name, total revenue, invoice count |

## Common Mistakes

**Mistake:** Using `invoice_list_sales` to find "top customers"
**Why it's wrong:** You'd have to aggregate yourself; `financial_sales_summary` does this already

**Mistake:** Using `financial_sales_summary` to find "unpaid invoices"
**Why it's wrong:** Summary doesn't show payment status; need `invoice_list_sales` with status filter
```

### Pattern 3: Confidence Indicator System
**What:** Two-level confidence system for tool recommendations.
**When to use:** Every row in the disambiguation matrix.
**Definition:**
```markdown
### Confidence Levels

| Level | Meaning | AI Agent Behavior |
|-------|---------|-------------------|
| **Definitive** | Tool is clearly the right choice for this question | Execute immediately |
| **Context-dependent** | Correct tool depends on additional user context | Ask clarifying question before executing |

**Definitive examples:**
- "Show invoice #123" → `invoice_get_detail` (unambiguous — specific invoice requested)
- "Test API connection" → `utility_test_connection` (only one tool for this)

**Context-dependent examples:**
- "Show me revenue" → Could be `financial_sales_summary` (totals) or `invoice_list_sales` (details)
- "Customer info" → Could be `contact_get_detail` (profile) or `contact_get_transactions` (history)
```

### Pattern 4: Entity-Based Organization for Overlaps
**What:** Group overlap discussions by primary business entity.
**When to use:** Match Phase 1 entity registry organization for consistency.
**Example:**
```markdown
## Tool Overlap Groups

### Contacts (Pelanggan/Vendor)
- `contact_list` vs `contact_get_detail` vs `contact_get_transactions`
- When tools overlap: All relate to "customer info" but serve different depths

### Invoices (Faktur)
- `invoice_list_sales` vs `invoice_list_purchase` — Direction (sales vs purchase)
- `invoice_list_sales` vs `financial_sales_summary` — Granularity (individual vs aggregated)
- `invoice_get_detail` vs `invoice_get_totals` — Scope (single vs summary)

### Orders (Pesanan)
- `order_list_sales` vs `order_list_purchase` — Direction
- `order_list_sales` vs `invoice_list_sales` — Stage in workflow (order precedes invoice)

### Financial (Keuangan)
- `financial_sales_summary` vs `financial_purchase_summary` — Direction
- `financial_bank_balances` — Unique (no overlap, definitive use case)
```

### Anti-Patterns to Avoid
- **Documenting every possible combination:** Focus on actually confusing overlaps, not all theoretically similar tools
- **Tool-centric instead of question-centric:** Users think in questions ("How much money?"), not tools ("Should I use financial_sales_summary?")
- **English-only business terminology:** Kledo is Indonesian software; include actual business terms users would type
- **Hiding alternatives:** Always show alternative tools when they exist — helps AI agents ask better clarifying questions
- **Missing parameter hints:** Include key parameters in the matrix to help with tool invocation

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tool discovery format | Custom JSON schema | llms.txt "Use for:" pattern | Already established in Phase 2, AI agents already parse it |
| Business question collection | Invent abstract questions | Use actual Kledo terminology | Indonesian users ask in specific ways |
| Overlap detection | Complex similarity algorithms | Manual curation | Only 23 tools; manual review is sufficient and more accurate |
| Matrix rendering | Custom HTML/JS | Markdown tables | Universal rendering, version control friendly |

**Key insight:** The 23-tool scale is small enough that manual curation produces better results than automated analysis. The matrix should be hand-written by someone who understands both the tools and the business domain.

## Common Pitfalls

### Pitfall 1: Forgetting the "Why" Behind Tool Selection
**What goes wrong:** Matrix says "use tool X" but doesn't explain why, making it hard to handle edge cases.
**Why it happens:** Rushing to create a lookup table without understanding the reasoning.
**How to avoid:** Every recommendation should be explainable in business terms (not just "use this tool for this query").
**Warning signs:** AI agents selecting wrong tools because they can't interpolate to similar questions.

### Pitfall 2: Stale Matrix After Tool Changes
**What goes wrong:** New tools added or tool behavior changed, but matrix not updated.
**Why it happens:** Matrix is manually maintained, separate from code.
**How to avoid:** Add matrix review to tool change checklist; consider generating skeleton from tool definitions.
**Warning signs:** llms.txt has tools not in matrix, or matrix references deprecated tools.

### Pitfall 3: Indonesian Terminology Mismatch
**What goes wrong:** Matrix uses formal Indonesian translations that don't match how Kledo users actually speak.
**Why it happens:** Direct translation instead of using actual Kledo UI terms.
**How to avoid:** Use terms from Kledo's actual UI and documentation: "faktur penjualan" (sales invoice), "pelanggan" (customer), "hutang" (receivable), "piutang" (payable).
**Warning signs:** Users typing queries that don't match any matrix entry.

### Pitfall 4: Over-Specification Leading to Rigidity
**What goes wrong:** Matrix tries to cover every possible phrasing, becoming unmaintainable.
**Why it happens:** Trying to achieve "complete" coverage.
**How to avoid:** Focus on 10-15 high-impact questions that cover 80% of use cases; AI agents can interpolate for variations.
**Warning signs:** Matrix with 100+ rows that still misses common queries.

### Pitfall 5: Missing the Context-Dependent Cases
**What goes wrong:** Everything marked "Definitive" even when clarification is needed.
**Why it happens:** Overconfidence in tool recommendations.
**How to avoid:** If the same question could reasonably use two tools, mark it "Context-dependent" and document when to ask for clarification.
**Warning signs:** AI agents confidently returning wrong results for ambiguous queries.

### Pitfall 6: Forgetting Cross-Entity Questions
**What goes wrong:** Matrix only handles single-entity questions, but users ask cross-entity questions.
**Why it happens:** Entity-based organization makes cross-entity questions fall through cracks.
**How to avoid:** Include a "Cross-Entity" section for questions like "Show customer X's invoices" (involves both Contact and Invoice).
**Warning signs:** Users need multiple tool calls for common workflows.

## Code Examples

Patterns for disambiguation documentation (no code — documentation only):

### Disambiguation Matrix Entry
```markdown
| What's my cash balance? / Berapa saldo kas? | `financial_bank_balances` | - | - | Definitive |
```

### Overlap Documentation Entry
```markdown
## invoice_list_sales vs financial_sales_summary

### TL;DR
- **invoice_list_sales**: "Show me the invoices" (individual records)
- **financial_sales_summary**: "How much did we sell?" (aggregated totals)

### Use invoice_list_sales when:
- You need specific invoice numbers
- You want to filter by status (paid, unpaid, overdue)
- You need to drill down to line items (via invoice_get_detail)

### Use financial_sales_summary when:
- You want revenue totals by customer
- You need to rank customers by sales volume
- You're comparing sales across time periods
```

### llms.txt Enhancement Pattern
```markdown
- [invoice_list_sales](docs/tools/sales/invoices.md#invoice_list_sales): List sales invoices. Use for: "show invoices", "unpaid invoices", "customer billing". See also: [disambiguation guide](docs/tools/disambiguation.md#invoice-tools)
```

### Bilingual Question Examples
```markdown
| English | Indonesian | Notes |
|---------|------------|-------|
| What's my revenue? | Berapa pendapatan saya? | Common question, definitive answer |
| Show unpaid invoices | Tampilkan faktur belum lunas | Status-based query |
| Who owes us money? | Siapa yang hutang ke kita? | Receivables question |
| Find customer Acme | Cari pelanggan Acme | Contact lookup |
| What did we buy from vendor X? | Apa yang kita beli dari vendor X? | Purchase invoice lookup |
| Check stock for product ABC | Cek stok produk ABC | Inventory question |
| What orders are pending? | Pesanan apa yang masih pending? | Order status query |
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single tool description | "Use for:" hints in llms.txt | llms.txt v1.0 (2026) | Better AI tool selection |
| Flat tool lists | Business question mapping | MCP ecosystem maturation | Query-first discovery |
| English-only docs | Bilingual support | Regional software adoption | Better local user experience |
| Tool-first documentation | Decision-tree documentation | 2025-2026 | Matches user mental model |

**Emerging patterns:**
- Control Plane as a Tool: Routing logic encapsulated behind single interface (for larger tool sets)
- MCP Tool Toolsets: Bounded, focused tool groups with clear domains
- llms.txt + llms-full.txt: Discovery file + detailed documentation split

**Not applicable at this scale:**
- Vector embeddings for tool selection (overkill for 23 tools)
- Automated disambiguation (manual curation more accurate)
- Complex routing algorithms (simple matrix lookup sufficient)

## Open Questions

Things that couldn't be fully resolved:

1. **Exact Indonesian phrasing preferences**
   - What we know: Kledo uses Indonesian terms like "faktur", "pelanggan", "hutang"
   - What's unclear: Exact phrasing Kledo users prefer (formal vs colloquial)
   - Recommendation: Start with terms from Kledo's own UI; iterate based on usage

2. **Optimal matrix granularity**
   - What we know: CONTEXT.md specifies 10-15 essential questions
   - What's unclear: Whether this is enough or if users have more variation
   - Recommendation: Start with 12-15 questions covering all domains; expand if gaps emerge

3. **llms.txt augmentation approach**
   - What we know: Phase 2 created llms.txt with "Use for:" hints
   - What's unclear: Whether to add disambiguation links or keep llms.txt minimal
   - Recommendation: Add "See also:" links to disambiguation guide for overlapping tools only

4. **Matrix validation methodology**
   - What we know: Matrix should help AI agents select correct tools
   - What's unclear: How to validate effectiveness before production use
   - Recommendation: Test with sample queries against Claude; iterate on failures

## Tool Inventory Analysis

Based on codebase review, here are the identified tool groups with overlap potential:

### High Overlap Potential
| Tool Pair | Overlap Reason | Disambiguation Key |
|-----------|----------------|-------------------|
| `invoice_list_sales` vs `financial_sales_summary` | Both answer "revenue" questions | Granularity: individual vs aggregated |
| `contact_list` vs `contact_get_detail` | Both answer "customer info" questions | Depth: list vs single |
| `invoice_list_sales` vs `invoice_list_purchase` | Both are invoice lists | Direction: sales (AR) vs purchase (AP) |
| `order_list_sales` vs `order_list_purchase` | Both are order lists | Direction: sales vs purchase |
| `invoice_list_sales` vs `order_list_sales` | Both sales-related, customer-focused | Stage: order precedes invoice |
| `product_list` vs `product_search_by_sku` | Both find products | Method: browse vs exact lookup |

### Low Overlap (Unique Purpose)
| Tool | Unique Purpose | Definitive Use Cases |
|------|---------------|---------------------|
| `financial_bank_balances` | Bank account balances | "Cash on hand", "Bank balance" |
| `financial_activity_team_report` | Team activity audit | "What did team do", "Activity log" |
| `delivery_get_pending` | Pending shipments | "What needs to ship", "Backlog" |
| `invoice_get_totals` | Invoice summary totals | "Total outstanding", "AR summary" |
| `utility_*` tools | Server operations | Cache, connection tests |

### Question Category Coverage

| Category | Count | Tools Involved |
|----------|-------|---------------|
| Reporting queries | 5 | financial_*, invoice_get_totals |
| Data lookup queries | 8 | *_list, *_get_detail, *_search |
| Analytical queries | 3 | financial_sales_summary, financial_purchase_summary, contact_get_transactions |
| Status/health queries | 4 | financial_bank_balances, delivery_get_pending, invoice_get_totals, utility_test_connection |

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/tools/*.py` — all 7 tool modules reviewed, 23 tools catalogued
- Phase 2 artifacts: `llms.txt`, `docs/tools/index.md` — existing documentation patterns
- Phase 1 entity registry: `src/entities/` — entity relationships and naming
- CONTEXT.md: User decisions on matrix structure, organization, bilingual support

### Secondary (MEDIUM confidence)
- [MCP Best Practices](https://mcp-best-practice.github.io/mcp-best-practice/best-practice/) — Tool design principles
- [MCP Tools Concepts](https://modelcontextprotocol.info/docs/concepts/tools/) — Tool specification patterns
- [llmstxt.org](https://llmstxt.org/) — llms.txt format specification
- [Decision Tree API Navigation](https://www.artima.com/articles/using-a-decision-tree-to-navigate-complex-apis) — Decision tree patterns for complex APIs
- [Kledo Software](https://kledo.com/) — Indonesian business terminology (faktur, pelanggan, hutang)

### Tertiary (LOW confidence)
- [AI Agent Routing Patterns](https://botpress.com/blog/ai-agent-routing) — General agent routing concepts
- [Google Multi-Agent Design Patterns](https://www.infoq.com/news/2026/01/multi-agent-design-patterns/) — Tool orchestration patterns (larger scale than needed)

## Metadata

**Confidence breakdown:**
- Matrix structure: HIGH — CONTEXT.md locked decisions, proven Markdown table patterns
- Overlap identification: HIGH — Manual review of 23 tools in codebase complete
- Indonesian terminology: MEDIUM — Based on Kledo website, may need user validation
- Optimal question count: MEDIUM — Following CONTEXT.md guidance (10-15), may need iteration

**Research date:** 2026-01-22
**Valid until:** 2026-04-22 (90 days — documentation patterns stable, tool inventory unlikely to change)

---

*Phase: 03-tool-enhancement*
*Research completed: 2026-01-22*
