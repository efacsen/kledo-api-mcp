# Roadmap: Kledo API MCP Server

## Milestones

- ✅ **v1.0 API Mapping & Smart Routing** - Phases 1-4 (shipped 2026-01-24)
- ✅ **v1.1 Analytics Foundation** - Phases 5-6 (shipped 2026-02-04)
- 🚧 **v1.2 Query Script Refactor** - Phases 7-10 (in progress)

## Phases

<details>
<summary>✅ v1.0 API Mapping & Smart Routing (Phases 1-4) - SHIPPED 2026-01-24</summary>

### Phase 1: Foundation - Entity Registry & Enhanced Descriptions
**Goal**: Establish single source of truth for entities and set quality bar for tool descriptions
**Plans**: 3 plans

Plans:
- [x] 01-01: Entity schema format and loader utility
- [x] 01-02: Core entity definitions with relationship mapping
- [x] 01-03: Enhanced tool descriptions with domain synonym dictionary

### Phase 2: Discovery - Documentation Layer & Tool Grouping
**Goal**: Add discoverability features that help agents understand tool relationships
**Plans**: 2 plans

Plans:
- [x] 02-01: Documentation enrichment system and business context
- [x] 02-02: MkDocs site with ERD diagrams

### Phase 3: Routing - Smart Tool Discovery
**Goal**: Intelligent routing using entity registry and enriched documentation
**Plans**: 2 plans

Plans:
- [x] 03-01: Keyword extraction and intent resolver
- [x] 03-02: Tool suggestion with confidence scoring

### Phase 4: Guidance - Workflows & AI-Optimized Docs
**Goal**: Workflow suggestions for common multi-step tasks
**Plans**: 2 plans

Plans:
- [x] 04-01: MCP Prompts for common workflows
- [x] 04-02: llms.txt documentation file

</details>

<details>
<summary>✅ v1.1 Analytics Foundation (Phases 5-6) - SHIPPED 2026-02-04</summary>

### Phase 5: Domain Model & Field Mapping
**Goal**: Convert confusing Kledo API field names to clear business terminology
**Plans**: 2 plans

Plans:
- [x] 05-01: Domain model definition with field mapping
- [x] 05-02: Conversion layer implementation

### Phase 6: Smart Onboarding
**Goal**: Guided setup and configuration wizard for new users
**Plans**: 2 plans

Plans:
- [x] 06-01: CLI wizard for initial setup
- [x] 06-02: Testing and diagnostics commands

</details>

### 🚧 v1.2 Query Script Refactor (In Progress)

**Milestone Goal:** Refactor query scripts into clean, dedicated per-entity scripts with consistent interfaces so atom AI agent can query Kledo data without confusion.

#### Phase 7: Infrastructure Foundation
**Goal**: Establish shared utilities and consistent interfaces for all query scripts
**Depends on**: Phase 6
**Requirements**: INF-01, INF-02, INF-03, INF-04, INF-05
**Success Criteria** (what must be TRUE):
  1. All scripts use consistent date filtering interface (date_from, date_to parameters)
  2. All scripts output monospace tables compatible with Telegram
  3. All scripts use compact currency formatting (99.2jt style)
  4. Shared utilities exist for common patterns (API calls, pagination, error handling)
  5. Import structure is clean and dependencies are explicit
**Plans**: TBD

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD
- [ ] 07-03: TBD

#### Phase 8: Core Entity Scripts
**Goal**: Dedicated scripts for core financial entities (invoices, purchase invoices, expenses, orders, purchase orders)
**Depends on**: Phase 7
**Requirements**: ENT-01, ENT-02, ENT-03, ENT-04, ENT-05
**Success Criteria** (what must be TRUE):
  1. User can query sales invoices via total_inv.py with date filtering
  2. User can query purchase invoices via total_pi.py with date filtering
  3. User can query expenses via total_exp.py with date filtering (new entity)
  4. User can query sales orders via total_order.py with date filtering
  5. User can query purchase orders via total_po.py with date filtering
  6. All entity scripts follow consistent output format (monospace tables, short currency)
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD
- [ ] 08-03: TBD

#### Phase 9: Analytics Scripts
**Goal**: Dedicated scripts for analytical queries (revenue, sales breakdown, outstanding, aging)
**Depends on**: Phase 8
**Requirements**: ANL-01, ANL-02, ANL-03, ANL-04
**Success Criteria** (what must be TRUE):
  1. User can get revenue summary via revenue_summary.py with date filtering
  2. User can get per-salesperson breakdown via sales_breakdown.py with date filtering
  3. User can get outstanding receivables via outstanding.py with date filtering
  4. User can get aging analysis via aging_report.py with date filtering
  5. All analytics scripts use entity scripts as building blocks (no duplicate logic)
**Plans**: TBD

Plans:
- [ ] 09-01: TBD
- [ ] 09-02: TBD

#### Phase 10: Cleanup & Migration
**Goal**: Remove bloated old modules and migrate MCP server to use new script structure
**Depends on**: Phase 9
**Requirements**: CLN-01, CLN-02, CLN-03, CLN-04, CLN-05
**Success Criteria** (what must be TRUE):
  1. Old bloated modules removed or refactored (invoices.py, revenue.py, sales_analytics.py)
  2. MCP server tool registration updated to use new scripts
  3. Smart routing recognizes new tool names
  4. All existing functionality preserved (no regressions)
  5. Codebase is cleaner with focused, maintainable scripts
**Plans**: TBD

Plans:
- [ ] 10-01: TBD
- [ ] 10-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 7 → 8 → 9 → 10

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-01-24 |
| 2. Discovery | v1.0 | 2/2 | Complete | 2026-01-24 |
| 3. Routing | v1.0 | 2/2 | Complete | 2026-01-24 |
| 4. Guidance | v1.0 | 2/2 | Complete | 2026-01-24 |
| 5. Domain Model | v1.1 | 2/2 | Complete | 2026-02-04 |
| 6. Onboarding | v1.1 | 2/2 | Complete | 2026-02-04 |
| 7. Infrastructure Foundation | v1.2 | 0/3 | Not started | - |
| 8. Core Entity Scripts | v1.2 | 0/3 | Not started | - |
| 9. Analytics Scripts | v1.2 | 0/2 | Not started | - |
| 10. Cleanup & Migration | v1.2 | 0/2 | Not started | - |
