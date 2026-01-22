# Phase 2: Documentation Layer - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate comprehensive, AI-readable API documentation from entity definitions. Create endpoint catalog, entity relationship docs, MkDocs site, and llms.txt for tool discovery. References entity registry from Phase 1.

</domain>

<decisions>
## Implementation Decisions

### Documentation format
- Hybrid approach: template markdown enhanced with auto-generated sections
- Auto-generated sections include both entity schemas and MCP tool signatures
- Organization by business domain (Sales, Purchases, Inventory, Finance)
- Standard example depth: one example request/response per tool

### llms.txt design
- Primary purpose: tool discovery (help AI find the right tool from natural language)
- Detailed verbosity: full descriptions with examples and disambiguation hints
- English only (Indonesian support deferred to Phase 4)
- Tools grouped by entity (all Invoice tools together, all Contact tools together)

### Entity relationship docs
- Dual visualization: Mermaid diagrams for simple views, erdantic for full ERD
- Relationship detail: show cardinality (one-to-many, many-to-many)
- Cross-references with context: links plus brief explanation of relationship
- Embedded types (e.g., InvoiceItem): separate section on parent page, not own pages

### MkDocs configuration
- Theme: Material for MkDocs (modern, feature-rich)
- Navigation: by business domain (matches documentation structure)
- Plugins: standard set (mermaid diagrams, auto-generated nav, code annotations)
- Deployment: GitHub Pages ready (include deployment config)

### Claude's Discretion
- Exact color scheme and styling
- Plugin version selections
- Directory structure under docs/
- Order of domains in navigation

</decisions>

<specifics>
## Specific Ideas

- llms.txt should help an AI agent answer "which tool do I use for X?" questions
- Entity pages should feel cohesive — embedded types stay with parent but are clearly delineated
- Documentation should be useful for both AI agents and human developers

</specifics>

<deferred>
## Deferred Ideas

- Indonesian business terms in llms.txt — Phase 4 (Smart Routing)
- Tool disambiguation matrix — Phase 3 (Tool Enhancement)
- Synonym dictionary — Phase 4 (Smart Routing)

</deferred>

---

*Phase: 02-documentation-layer*
*Context gathered: 2026-01-22*
