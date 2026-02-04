# Kledo API MCP Server

## What This Is

MCP (Model Context Protocol) server yang menghubungkan AI agents dengan Kledo accounting software. Server ini menyediakan self-documenting API layer dengan intelligent natural language routing, sehingga AI agents (Claude Code, atau agent lain) dapat dengan mudah mengakses dan memahami data bisnis dari Kledo — tanpa perlu manual export CSV lagi.

v1.0 includes: Entity registry, comprehensive documentation layer, tool disambiguation, and bilingual smart routing.
v1.1 includes: Domain model with clear business terminology, smart onboarding wizard.

## Current Milestone: v1.2 Query Script Refactor

**Goal:** Refactor query scripts into clean, dedicated per-entity scripts so atom doesn't get confused when users query Kledo data. Each entity type gets its own focused script with consistent date filtering.

**Target features:**
- Dedicated per-entity query scripts (total_inv.py, total_pi.py, total_exp.py, etc.)
- Consistent date filtering across all scripts
- Clean, less confusing structure for AI agent consumption
- Proper Telegram-friendly output formatting (monospace code blocks)

## Core Value

AI agents dapat langsung query data bisnis real-time dari Kledo dengan tau persis endpoint mana yang dipakai, tanpa perlu memahami kompleksitas API documentation Kledo yang membingungkan.

## Requirements

### Validated

- ✓ Authentication via email/password — existing
- ✓ Financial reports (profit/loss, balance sheet, cash flow) — existing
- ✓ Invoice management (list, detail, totals) — existing
- ✓ Order management (sales & purchase orders) — existing
- ✓ Product catalog & inventory — existing
- ✓ Contact/customer management — existing
- ✓ Delivery tracking — existing
- ✓ Bank transactions & balances — existing
- ✓ Account management — existing
- ✓ Caching layer with TTL — existing
- ✓ Entity relationship documentation (semua entity dan relasinya) — v1.0
- ✓ API endpoint catalog (dokumentasi endpoint apa untuk operasi apa) — v1.0
- ✓ Visual ERD diagram (diagram relasi antar entity) — v1.0
- ✓ Enhanced tool descriptions (rich context untuk AI) — v1.0
- ✓ Business term mapping (simple routing layer) — v1.0

### Active

- [ ] Dedicated per-entity query scripts with date filtering
- [ ] Expenses/biaya tools (total_exp.py)
- [ ] Clean tool structure — one script per entity type
- [ ] Consistent output formatting (monospace, short currency)
- [ ] Operation cost tools

### Out of Scope

- Full semantic search with vector embeddings — overkill untuk ~30 tools, simple keyword mapping cukup
- Real-time sync/webhooks — fokus pull-based queries dulu
- Multi-tenant support — single company (PT Cepat Service Station) only
- Write operations (create/update) — fokus read/query dulu untuk reporting

## Context

**Current State (v1.1):**
- Shipped self-documenting MCP server with 30+ tools
- Complete entity registry with Pydantic models
- MkDocs documentation site with ERD generation
- Bilingual smart routing (Indonesian/English)
- Domain model with clear business terminology (InvoiceFinancials)
- Smart onboarding wizard (--setup, --test, --show-config)
- Telegram-friendly monospace formatting + short currency (99.2jt)
- Codebase: 9 tool modules, 4,033 lines across tools

**Business Context:**
- Kledo adalah CRM akuntansi yang dipakai untuk manage semua data perusahaan
- Current pain: Manual export CSV → proses di Python → data tidak real-time
- API documentation Kledo membingungkan, susah pinpoint endpoint yang tepat

**Technical Context:**
- Existing MCP server sudah berjalan dengan 7 tool modules
- Python-based dengan async/await pattern
- Config-driven endpoint mapping (endpoints.yaml)
- Multi-tier caching dengan TTL per category
- Authentication: Bearer token via email/password login
- Tech stack: FastMCP, Pydantic, MkDocs Material, RapidFuzz

**User Context:**
- Primary user: Single developer (personal use)
- Familiar dengan Kledo dari UI perspective, less familiar dengan API structure
- Use cases: Reporting/analytics, automation, data lookup, AI assistant

## Constraints

- **API**: Kledo REST API — harus follow API structure mereka
- **Auth**: Email/password based (token refresh otomatis)
- **Base URL**: https://ptcepatservicestation.api.kledo.com/api/v1
- **Compatibility**: Harus compatible dengan existing MCP tools yang sudah jalan

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Embedded + Simple Routing | Balance simplicity dan power; vector search overkill untuk 30 tools | ✓ Good — v1.0 proved pattern matching + synonyms sufficient |
| Map first, extend later | Understand full API landscape before adding new tools | ✓ Good — Entity registry enabled documentation layer |
| Focus on read operations | Reporting adalah primary use case, write ops bisa ditambah nanti | ✓ Good — All v1.0 requirements met without write ops |
| Pydantic models for entities | Type-safe entity definitions with relationship metadata | ✓ Good — Enabled ERD generation and clear API contracts |
| MkDocs Material for docs | Native Mermaid support over plugin alternatives | ✓ Good — Clean docs with zero config overhead |
| Bilingual synonym dictionary | Support Indonesian + English business terms | ✓ Good — 50 terms covers most common queries |
| Pattern matching precedence | Idiomatic expressions matched before keyword scoring | ✓ Good — "outstanding invoices" → direct tool match |
| 80% fuzzy match threshold | Balance typo tolerance with precision | ✓ Good — "invoise" matches "invoice" at 85.7% |

| Per-entity scripts | Atom gets confused with current multi-function modules; dedicated scripts are clearer | — Pending |
| Monospace + short currency | Telegram can't render markdown tables; use code blocks + compact numbers | ✓ Good — deployed to VPS |

---
*Last updated: 2026-02-04 after v1.2 milestone start*
