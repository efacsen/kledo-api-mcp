# Requirements: Kledo API MCP Server — v1.2 Query Script Refactor

**Defined:** 2026-02-04
**Core Value:** AI agents can query Kledo data without confusion — one script per entity, consistent interface

## v1.2 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Entity Scripts

- [ ] **ENT-01**: Dedicated `total_inv.py` script for sales invoices — list, totals, detail with date filtering
- [ ] **ENT-02**: Dedicated `total_pi.py` script for purchase invoices — list, totals with date filtering
- [ ] **ENT-03**: Dedicated `total_exp.py` script for expenses/biaya — list, totals with date filtering (NEW entity)
- [ ] **ENT-04**: Dedicated `total_order.py` script for sales orders with date filtering
- [ ] **ENT-05**: Dedicated `total_po.py` script for purchase orders with date filtering

### Analytics Scripts

- [ ] **ANL-01**: Dedicated `revenue_summary.py` script for revenue overview with date filtering
- [ ] **ANL-02**: Dedicated `sales_breakdown.py` script for per-sales-person breakdown with date filtering
- [ ] **ANL-03**: Dedicated `outstanding.py` script for outstanding receivables (piutang) with date filtering
- [ ] **ANL-04**: Dedicated `aging_report.py` script for aging analysis with date filtering

### Infrastructure

- [ ] **INF-01**: Consistent date filtering interface across all scripts (date_from, date_to params)
- [ ] **INF-02**: All scripts use `format_currency(short=True)` for compact output
- [ ] **INF-03**: All scripts use monospace `format_markdown_table()` for Telegram-compatible output
- [ ] **INF-04**: Shared base class or utilities for common patterns (API calls, pagination, error handling)
- [ ] **INF-05**: Clean import structure — each script is self-contained with clear dependencies

### Cleanup

- [ ] **CLN-01**: Remove or refactor bloated modules (invoices.py: 1000 lines → split into focused scripts)
- [ ] **CLN-02**: Remove or refactor revenue.py (909 lines → split into focused scripts)
- [ ] **CLN-03**: Remove or refactor sales_analytics.py (504 lines → split into focused scripts)
- [ ] **CLN-04**: Update MCP server tool registration to use new script structure
- [ ] **CLN-05**: Update routing/smart routing to recognize new tool names

## Future Requirements

Deferred to later milestones.

### Extended Entity Coverage

- **FUT-01**: Operation cost tools (biaya operasional)
- **FUT-02**: Bank transaction scripts
- **FUT-03**: Delivery tracking scripts
- **FUT-04**: Product/inventory scripts

### Advanced Analytics

- **FUT-05**: Customer concentration report (Pareto)
- **FUT-06**: Daily breakdown with trend analysis
- **FUT-07**: Team activity/performance report

## Out of Scope

| Feature | Reason |
|---------|--------|
| Write operations (create/update invoices) | Read-only focus for reporting — v2+ |
| Real-time webhooks | Pull-based queries sufficient for current needs |
| Multi-tenant support | Single company only (PT CSS) |
| Full 323 endpoint coverage | Focus on high-value entities first |
| New UI/dashboard | Scripts are consumed by AI agents, not humans directly |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| (To be filled by roadmap) | | |

**Coverage:**
- v1.2 requirements: 18 total
- Mapped to phases: 0
- Unmapped: 18 ⚠️

---
*Requirements defined: 2026-02-04*
*Last updated: 2026-02-04 after initial definition*
