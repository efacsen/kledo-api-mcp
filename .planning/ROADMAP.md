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

### Phase 6: Smart MCP Server Onboarding

**Goal:** Reduce setup from 5+ steps to one-command first-run, with wizard-based configuration

**Depends on:** Phase 5 complete

**Plans:** 3 plans

Plans:
- [ ] 06-01-PLAN.md - Implement setup wizard and first-run detection
- [ ] 06-02-PLAN.md - Add validation commands (--setup, --test, --show-config)
- [ ] 06-03-PLAN.md - Update README with quick-start guide and copy-paste Claude config

**Details:**

Build intelligent onboarding that guides new users through setup without manual config file edits:

**First-Run Experience:**
```bash
kledo-mcp  # First time: interactive setup wizard
# → Prompts for API key
# → Creates .env
# → Tests connection
# → Shows Claude Desktop config
# → Saves preferences

kledo-mcp  # Every other time: just works
```

**Setup Commands:**
- `kledo-mcp --setup` - Explicit setup wizard (for documentation/redoing setup)
- `kledo-mcp --test` - Validate connection to Kledo API
- `kledo-mcp --show-config` - Print Claude Desktop config to copy
- `kledo-mcp --init` - Force first-run setup again

**Deliverables:**
- `src/setup.py` - Setup wizard + first-run detection
- `src/config_manager.py` - Configuration creation/validation
- `src/cli.py` - Command-line argument handling
- Updated entry point to detect first-run
- Updated README with "Quick Start in 2 minutes" section

**Why this matters:**
- Current setup requires: copy .env.example, edit .env, find Claude config path, edit JSON, restart Claude
- Users get confused at "edit JSON" step (paths, syntax, where to find config)
- Onboarding friction means lower adoption
- 15 minutes of dev time saves hours of user support emails

**UX Goals:**
- Zero manual JSON editing required
- Clear prompts with helpful context
- Color-coded output (green=success, red=error, yellow=warning)
- Copy-paste friendly configuration blocks
- Validation feedback before starting server

**Success criteria:**
- New user can run `kledo-mcp` and be connected in < 2 minutes
- `--setup` wizard is idempotent (can run multiple times safely)
- Connection test validates both auth and API access
- Claude Desktop config printed with copy-to-clipboard support
- README has "30-second setup" section with one command

**Time estimate:** 6 hours (1-2 days)
**Priority:** MEDIUM - Improves user experience significantly

**Context docs:**
- Current setup process documented in README.md lines 90-173
- .env.example shows required variables
- pyproject.toml shows entry point configuration

---
