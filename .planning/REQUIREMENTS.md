# Requirements: Kledo API MCP Server Mapping

**Defined:** 2026-01-21
**Core Value:** AI agents can directly query Kledo business data with clear understanding of which endpoint to use

## v1 Requirements

Requirements for comprehensive API mapping and smart routing.

### Entity Registry

- [ ] **ENTY-01**: Define all Kledo entities in YAML format (Invoice, Contact, Product, Order, Delivery, Account, Bank, etc.)
- [ ] **ENTY-02**: Map relationships between entities (Invoice → Contact, Order → Product, etc.)
- [ ] **ENTY-03**: Generate visual ERD diagram from entity definitions

### Tool Enhancement

- [ ] **TOOL-01**: Create tool disambiguation matrix showing which tool for which use case
- [ ] **TOOL-02**: Document tool overlaps and when to use each (e.g., invoice_list vs financial_sales_summary)

### Documentation

- [ ] **DOCS-01**: Create API endpoint catalog (endpoint → operation mapping)
- [ ] **DOCS-02**: Write entity relationship documentation in Markdown
- [ ] **DOCS-03**: Setup MkDocs with Material theme for auto-generated docs
- [ ] **DOCS-04**: Generate llms.txt for AI-optimized discovery

### Smart Routing

- [ ] **ROUT-01**: Build synonym dictionary for business terms (revenue=sales, vendor=supplier, bill=invoice)
- [ ] **ROUT-02**: Implement tool discovery/search capability
- [ ] **ROUT-03**: Add intent-to-tool resolution (natural language → tool + parameters)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Tool Enhancement

- **TOOL-03**: Enhance all tool descriptions to <150 tokens with rich context
- **TOOL-04**: Add complete parameter documentation with examples for all tools
- **TOOL-05**: Implement structured error responses across all tools
- **TOOL-06**: Add cross-references between related tools

### Additional API Coverage

- **API-01**: Add Expenses/Biaya tools
- **API-02**: Add Operation Cost tools
- **API-03**: Coverage for remaining Kledo API endpoints

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Vector/semantic search | Overkill for ~30 tools; simple keyword matching sufficient |
| Dynamic tool loading | Under 50K token overhead, not needed |
| Write operations (create/update) | Focus on read/query for reporting first |
| Multi-tenant support | Single company use only |
| Real-time webhooks | Pull-based queries sufficient for current needs |
| Comprehensive API coverage (all 323 endpoints) | Demand-driven, add as needed |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENTY-01 | TBD | Pending |
| ENTY-02 | TBD | Pending |
| ENTY-03 | TBD | Pending |
| TOOL-01 | TBD | Pending |
| TOOL-02 | TBD | Pending |
| DOCS-01 | TBD | Pending |
| DOCS-02 | TBD | Pending |
| DOCS-03 | TBD | Pending |
| DOCS-04 | TBD | Pending |
| ROUT-01 | TBD | Pending |
| ROUT-02 | TBD | Pending |
| ROUT-03 | TBD | Pending |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 0
- Unmapped: 12 ⚠️

---
*Requirements defined: 2026-01-21*
*Last updated: 2026-01-21 after initial definition*
