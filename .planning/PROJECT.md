# Kledo API MCP Server

## What This Is

MCP (Model Context Protocol) server yang menghubungkan AI agents dengan Kledo accounting software. Server ini menyediakan comprehensive mapping dari Kledo API sehingga AI agents (Claude Code, atau agent lain) dapat dengan mudah mengakses dan memahami data bisnis dari Kledo — tanpa perlu manual export CSV lagi.

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

### Active

- [ ] Entity relationship documentation (semua entity dan relasinya)
- [ ] API endpoint catalog (dokumentasi endpoint apa untuk operasi apa)
- [ ] Visual ERD diagram (diagram relasi antar entity)
- [ ] Enhanced tool descriptions (rich context untuk AI)
- [ ] Business term mapping (simple routing layer)
- [ ] Expenses/biaya tools
- [ ] Operation cost tools

### Out of Scope

- Full semantic search with vector embeddings — overkill untuk ~30 tools, simple keyword mapping cukup
- Real-time sync/webhooks — fokus pull-based queries dulu
- Multi-tenant support — single company (PT Cepat Service Station) only
- Write operations (create/update) — fokus read/query dulu untuk reporting

## Context

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
| Embedded + Simple Routing | Balance simplicity dan power; vector search overkill untuk 30 tools | — Pending |
| Map first, extend later | Understand full API landscape before adding new tools | — Pending |
| Focus on read operations | Reporting adalah primary use case, write ops bisa ditambah nanti | — Pending |

---
*Last updated: 2026-01-21 after initialization*
