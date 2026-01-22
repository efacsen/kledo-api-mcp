# Roadmap: Kledo API MCP Server

## Overview

This roadmap transforms the existing Kledo MCP server (30+ tools) into a self-documenting, discoverable API layer. The journey progresses from establishing a foundational entity registry, through comprehensive documentation generation, to tool disambiguation, and finally intelligent routing - each phase building on the previous to deliver increasingly powerful AI agent capabilities.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Entity Registry** - Establish single source of truth for all Kledo entities and relationships
- [x] **Phase 2: Documentation Layer** - Generate comprehensive API documentation from entity definitions
- [ ] **Phase 3: Tool Enhancement** - Create disambiguation matrix and document tool overlaps
- [ ] **Phase 4: Smart Routing** - Implement intelligent tool discovery from natural language queries

## Phase Details

### Phase 1: Entity Registry
**Goal**: Establish a complete, machine-readable catalog of all Kledo entities and their relationships using Pydantic models
**Depends on**: Nothing (first phase)
**Requirements**: ENTY-01, ENTY-02, ENTY-03
**Success Criteria** (what must be TRUE):
  1. All Kledo entities (Invoice, Contact, Product, Order, Delivery, Account) are defined as Pydantic models with fields and types
  2. Relationships between entities are explicitly mapped via Field metadata (e.g., Invoice references Contact, Order contains Products)
  3. A visual ERD diagram can be generated from the entity definitions using erdantic
  4. Entity definitions are loadable by Python code via `get_all_entities()` and `get_entity_class()`
**Plans**: 3 plans in 2 waves

Plans:
- [x] 01-01-PLAN.md - Core entity models (Contact, Product, Invoice) + package structure
- [x] 01-02-PLAN.md - Transaction entity models (Order, Delivery, Account)
- [x] 01-03-PLAN.md - Entity loader utilities + YAML export + ERD generation

### Phase 2: Documentation Layer
**Goal**: Generate comprehensive, AI-readable API documentation from entity definitions
**Depends on**: Phase 1 (Entity Registry must exist for documentation to reference)
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04
**Success Criteria** (what must be TRUE):
  1. API endpoint catalog exists mapping each endpoint to its operation and entity
  2. Entity relationship documentation is available in Markdown format
  3. MkDocs site generates and serves documentation locally
  4. llms.txt file exists with AI-optimized tool discovery information
  5. Documentation references entity definitions from Phase 1
**Plans**: 3 plans in 2 waves

Plans:
- [x] 02-01-PLAN.md - MkDocs setup + entity documentation with Mermaid ERDs
- [x] 02-02-PLAN.md - Tool extraction script + domain-organized tool documentation
- [x] 02-03-PLAN.md - llms.txt + getting-started guide + GitHub Pages deployment

### Phase 3: Tool Enhancement
**Goal**: Clarify tool selection by documenting overlaps and creating a disambiguation matrix
**Depends on**: Phase 2 (needs documentation context to explain tool purposes)
**Requirements**: TOOL-01, TOOL-02
**Success Criteria** (what must be TRUE):
  1. Tool disambiguation matrix shows which tool to use for each common use case
  2. Tool overlap documentation explains when to use similar tools (e.g., invoice_list vs financial_sales_summary)
  3. Each tool's unique purpose is clearly distinguished from related tools
**Plans**: TBD

Plans:
- [ ] 03-01: TBD

### Phase 4: Smart Routing
**Goal**: Enable AI agents to find the right tool from natural language business queries
**Depends on**: Phase 1, 2, 3 (uses entities, documentation, and disambiguation for full context)
**Requirements**: ROUT-01, ROUT-02, ROUT-03
**Success Criteria** (what must be TRUE):
  1. Synonym dictionary covers common business terms (revenue/sales, vendor/supplier, bill/invoice, customer/client)
  2. Tool search capability returns relevant tools for keyword queries
  3. Natural language queries resolve to specific tools with suggested parameters
  4. Indonesian business terms are supported (faktur, tagihan, piutang, saldo, kas)
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Entity Registry | 3/3 | Complete | 2026-01-22 |
| 2. Documentation Layer | 3/3 | Complete | 2026-01-22 |
| 3. Tool Enhancement | 0/? | Not started | - |
| 4. Smart Routing | 0/? | Not started | - |

---
*Roadmap created: 2026-01-21*
*Last updated: 2026-01-22*
