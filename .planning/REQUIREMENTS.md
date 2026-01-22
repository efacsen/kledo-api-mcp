# Requirements: Kledo API MCP Server Mapping

**Defined:** 2026-01-21
**Core Value:** AI agents can directly query Kledo business data with clear understanding of which endpoint to use

## v1 Requirements

Requirements for comprehensive API mapping and smart routing.

### Entity Registry

- [x] **ENTY-01**: Define all Kledo entities in YAML format (Invoice, Contact, Product, Order, Delivery, Account, Bank, etc.)
- [x] **ENTY-02**: Map relationships between entities (Invoice -> Contact, Order -> Product, etc.)
- [x] **ENTY-03**: Generate visual ERD diagram from entity definitions

### Tool Enhancement

- [x] **TOOL-01**: Create tool disambiguation matrix showing which tool for which use case
- [x] **TOOL-02**: Document tool overlaps and when to use each (e.g., invoice_list vs financial_sales_summary)

### Documentation

- [x] **DOCS-01**: Create API endpoint catalog (endpoint -> operation mapping)
- [x] **DOCS-02**: Write entity relationship documentation in Markdown
- [x] **DOCS-03**: Setup MkDocs with Material theme for auto-generated docs
- [x] **DOCS-04**: Generate llms.txt for AI-optimized discovery

### Smart Routing

- [ ] **ROUT-01**: Build synonym dictionary for business terms (revenue=sales, vendor=supplier, bill=invoice)
- [ ] **ROUT-02**: Implement tool discovery/search capability
- [ ] **ROUT-03**: Add intent-to-tool resolution (natural language -> tool + parameters)

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
| ENTY-01 | Phase 1 | Complete |
| ENTY-02 | Phase 1 | Complete |
| ENTY-03 | Phase 1 | Complete |
| DOCS-01 | Phase 2 | Complete |
| DOCS-02 | Phase 2 | Complete |
| DOCS-03 | Phase 2 | Complete |
| DOCS-04 | Phase 2 | Complete |
| TOOL-01 | Phase 3 | Complete |
| TOOL-02 | Phase 3 | Complete |
| ROUT-01 | Phase 4 | Pending |
| ROUT-02 | Phase 4 | Pending |
| ROUT-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0

---
*Requirements defined: 2026-01-21*
*Last updated: 2026-01-22 after Phase 3 completion*
