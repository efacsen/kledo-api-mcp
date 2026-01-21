# Phase 1: Entity Registry - Context

**Gathered:** 2026-01-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish a complete, machine-readable catalog of all Kledo entities and their relationships. Defines the data model foundation that downstream phases (documentation, tool enhancement, smart routing) will build upon.

**In scope:** Entity definitions, field metadata, relationships, YAML schemas, Python loader
**Out of scope:** API endpoint mappings, documentation generation, Indonesian translations

</domain>

<decisions>
## Implementation Decisions

### Schema format
- Follow OpenAPI/JSON Schema conventions for type definitions
- Claude's discretion: YAML structure (flat vs grouped), whether to combine or separate API mappings

### Relationship modeling
- Claude's discretion: Inline references vs separate relationships section
- Claude's discretion: Level of relationship metadata (basic cardinality vs extended)
- Claude's discretion: Whether ERD generation belongs in this phase or Phase 2
- Relationships will be reviewed by user after initial generation from existing tools

### Field metadata
- Full context for each field: name, type, required, description, example, api_name (if different), default_value, constraints, business_meaning
- Descriptions include both business-focused explanation AND technical notes
- Example values should use real data from actual Kledo API responses (user will provide sample invoice data)
- Indonesian translations deferred to Phase 4 (Smart Routing)

### File organization
- Location: `src/entities/` — keep schemas close to Python code
- Include Python loader module with `load_entity()`, `get_all_entities()` functions
- Validate YAML files against JSON Schema on load for data integrity

</decisions>

<specifics>
## Specific Ideas

- User will provide real invoice data from Kledo API as reference for field examples and structure
- Validation should catch schema errors early during development

</specifics>

<deferred>
## Deferred Ideas

- Indonesian business term translations (faktur, tagihan, piutang) — Phase 4: Smart Routing

</deferred>

---

*Phase: 01-entity-registry*
*Context gathered: 2026-01-21*
