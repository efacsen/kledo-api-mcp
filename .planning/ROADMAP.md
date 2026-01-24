# Kledo API MCP Server - Roadmap

## Current Milestone: v1.1 Analytics Foundation

**Goal:** Build professional analytics platform with clear domain model and optimized tool architecture

**Status:** Planning
**Started:** 2026-01-24
**Target:** 2-3 weeks

---

## Phases

### Phase 5: Domain Model & Field Mapping

**Goal:** Convert confusing Kledo API field names to clear business terminology

**Depends on:** v1.0 complete

**Plans:** 2 plans

Plans:
- [ ] 05-01-PLAN.md - Create domain model (InvoiceFinancials) + mapper + tests
- [ ] 05-02-PLAN.md - Update tools (revenue, invoices, sales_analytics) to use domain model

**Details:**

Implement conversion layer that maps Kledo fields to domain model:
- `amount_after_tax` -> `gross_sales` (Penjualan Bruto)
- `subtotal` -> `net_sales` (Penjualan Neto)
- `total_tax` -> `tax_collected` (PPN)

Deliverables:
- `src/models/invoice_financials.py` - Domain model classes
- `src/mappers/kledo_mapper.py` - Conversion functions
- `tests/test_kledo_mapper.py` - Validation tests
- Updated tools: revenue, invoices, sales_analytics

**Why this matters:**
- Field validation with 5 invoices proved: `subtotal + total_tax = amount_after_tax`
- Kledo's naming is confusing: "after_tax" sounds like subtraction but means addition
- 8-hour investment saves 100+ hours in developer confusion
- Finance team can read code directly with proper terminology

**Technical debt resolved:**
- Removes confusion from raw API field names
- Professional code quality
- Easier onboarding for new developers
- Clear communication with finance team

**Success criteria:**
- All tests pass
- Revenue report uses `gross_sales` not `amount_after_tax`
- Code self-documenting with business terms
- Zero ambiguity in field meanings

**Time estimate:** 8 hours (2-3 days)
**Priority:** HIGH - Foundation for all future analytics

**Context docs:**
- `docs/technical/SESSION_HANDOFF.md` - Full implementation context
- `docs/technical/FIELD_MAPPING_DECISION.md` - Architecture rationale
- `docs/technical/QUICK_DECISIONS_SUMMARY.md` - Quick reference
- `tests/validate_invoice_fields.py` - Field validation proof

---
