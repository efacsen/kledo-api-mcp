# Architecture Research: API Entity Mapping, Documentation, and Routing Layers

**Project:** Kledo API MCP Server - Enhanced Mapping
**Research Date:** 2026-01-21
**Confidence:** HIGH (based on existing codebase analysis + MCP documentation)

---

## Executive Summary

This research examines how to add entity mapping, documentation, and smart routing layers to the existing Kledo MCP server. The current architecture is well-structured with clear separation of concerns (Transport -> Auth -> Client -> Cache -> Tools). New components should follow this pattern and integrate at specific points rather than requiring architectural rewrites.

**Key recommendation:** Add three new layers that integrate with existing architecture:
1. **Entity Registry** - Central catalog of API entities and relationships
2. **Documentation Layer** - Rich context for tools and entities
3. **Routing Layer** - Simple keyword-to-tool mapping for natural language queries

---

## Component Overview

### New Components Needed

| Component | Purpose | Integration Point |
|-----------|---------|-------------------|
| **Entity Registry** | Catalog of all Kledo API entities (invoices, contacts, products, etc.) with their relationships | Standalone data files, consumed by tools and docs |
| **Documentation Layer** | Rich descriptions, examples, business context for each entity and tool | Tool definitions + separate docs |
| **Routing Layer** | Maps business terms to appropriate tools | Server-level, before tool dispatch |

### Why These Three

The project requirements specify:
- Entity relationship documentation
- API endpoint catalog
- Enhanced tool descriptions
- Business term mapping

These map naturally to three components:
- Entity Registry handles entity relationships and endpoint catalog
- Documentation Layer handles enhanced descriptions and examples
- Routing Layer handles business term mapping

---

## Integration with Existing Architecture

### Current Data Flow

```
AI Agent (Claude)
    |
    | MCP Protocol (stdio)
    v
+-------------------------------------------+
|           MCP Server (server.py)          |
|  +-------------------------------------+  |
|  |   Tool Registry & Router            |  |
|  |   - list_tools()                    |  |
|  |   - call_tool(name, args)           |  |
|  +-------------------------------------+  |
+-------------------------------------------+
                    |
    +---------------+---------------+
    |                               |
    v                               v
Tool Handlers                   Utilities
(financial, invoices,           (logger, helpers)
 orders, products,
 contacts, deliveries)
    |
    v
+-------------------------------------------+
|        Kledo API Client (kledo_client.py) |
|  +-------------+    +------------------+  |
|  | Request Mgr | -> | Cache Manager    |  |
|  +-------------+    +------------------+  |
+-------------------------------------------+
    |
    v
+-------------------------------------------+
|       Auth Layer (auth.py)                |
+-------------------------------------------+
    |
    v
        Kledo REST API
```

### Proposed Enhanced Data Flow

```
AI Agent (Claude)
    |
    | MCP Protocol (stdio)
    v
+-------------------------------------------+
|           MCP Server (server.py)          |
|  +-------------------------------------+  |
|  |   Enhanced Tool Registry            |  |<--- Documentation Layer
|  |   - list_tools() [enriched]         |  |     (provides rich tool descriptions)
|  |   - call_tool(name, args)           |  |
|  +-------------------------------------+  |
|  +-------------------------------------+  |
|  |   Routing Layer (NEW)               |  |
|  |   - resolve_intent(query) -> tool   |  |
|  +-------------------------------------+  |
+-------------------------------------------+
                    |
    +---------------+---------------+
    |                               |
    v                               v
Tool Handlers                   Entity Registry (NEW)
(financial, invoices,           - entity definitions
 orders, products,              - relationships
 contacts, deliveries)          - field mappings
    |                               |
    +---------------+---------------+
                    |
                    v
+-------------------------------------------+
|        Kledo API Client (kledo_client.py) |
|  +-------------+    +------------------+  |
|  | Request Mgr | -> | Cache Manager    |  |
|  +-------------+    +------------------+  |
+-------------------------------------------+
    |
    v
         (unchanged below)
```

### Integration Points

| New Component | Integrates With | How |
|---------------|-----------------|-----|
| Entity Registry | Tool handlers | Tools import entity definitions for validation/context |
| Entity Registry | Documentation Layer | Docs reference entity definitions for consistency |
| Documentation Layer | Tool definitions | Enriches `Tool.description` and `inputSchema` |
| Documentation Layer | Server `list_tools()` | Returns enhanced tool metadata |
| Routing Layer | Server `call_tool()` | Pre-processes requests to suggest/route tools |

---

## Data Flow

### Entity Resolution Flow

When a tool needs entity information:

```
Tool Handler (e.g., invoices.py)
    |
    | import entity definition
    v
Entity Registry (entities/invoice.yaml)
    |
    | Returns: fields, relationships, validation rules
    v
Tool Handler
    |
    | Uses for: validation, formatting, context
    v
Response to AI Agent
```

### Documentation Enhancement Flow

When AI requests tool list:

```
AI Agent calls list_tools()
    |
    v
Server.list_tools()
    |
    | For each tool module
    v
Tool Module get_tools()
    |
    | Returns base Tool definitions
    v
Documentation Layer enhances
    |
    | Adds: rich descriptions, examples, entity context
    v
Enhanced Tool list returned
```

### Smart Routing Flow

When AI makes natural language query:

```
AI Agent: "Show me unpaid invoices"
    |
    | Tool call: potentially wrong tool or generic query
    v
Routing Layer
    |
    | Keyword matching: "unpaid" + "invoices" -> invoice_list_sales with status filter
    v
Suggested tool + parameters
    |
    v
Tool execution
```

---

## Build Order

### Phase 1: Entity Registry (Foundation)

**Build first because:** All other components depend on entity definitions.

Components:
1. Entity schema format (YAML structure)
2. Entity loader utility
3. Core entity definitions (Invoice, Contact, Product, Order)
4. Relationship mapping

**Files to create:**
```
src/entities/
  __init__.py
  schema.py          # Entity schema definitions
  loader.py          # YAML loader

config/entities/
  invoice.yaml
  contact.yaml
  product.yaml
  order.yaml
  account.yaml
  relationships.yaml # Cross-entity relationships
```

**Integration:** Minimal - standalone data files that can be imported.

### Phase 2: Documentation Layer

**Build second because:** Uses Entity Registry, enhances existing tools.

Components:
1. Documentation schema format
2. Tool enrichment system
3. Example generator
4. Business context definitions

**Files to create/modify:**
```
src/docs/
  __init__.py
  enricher.py        # Tool description enricher
  examples.py        # Example generator
  business_terms.py  # Business term glossary

config/docs/
  tool_docs.yaml     # Extended tool documentation
  business_context.yaml  # Domain-specific context
```

**Integration:** Modifies `get_tools()` return values in each tool module.

### Phase 3: Routing Layer

**Build third because:** Uses both Entity Registry and Documentation for context.

Components:
1. Keyword extractor
2. Intent resolver
3. Tool suggester
4. Parameter inferencer

**Files to create/modify:**
```
src/routing/
  __init__.py
  keywords.py        # Keyword extraction
  resolver.py        # Intent to tool mapping
  suggester.py       # Tool suggestions

config/routing/
  keyword_map.yaml   # Keyword -> tool mappings
  synonyms.yaml      # Business term synonyms
```

**Integration:** Hooks into `server.py` at the `call_tool()` level.

---

## File Structure

### Recommended Final Structure

```
kledo-api-mcp/
├── config/
│   ├── endpoints.yaml        # (existing) API endpoint mappings
│   ├── cache_config.yaml     # (existing) Cache TTL settings
│   ├── entities/             # (NEW) Entity definitions
│   │   ├── invoice.yaml
│   │   ├── contact.yaml
│   │   ├── product.yaml
│   │   ├── order.yaml
│   │   ├── delivery.yaml
│   │   ├── account.yaml
│   │   ├── bank.yaml
│   │   └── relationships.yaml
│   ├── docs/                 # (NEW) Documentation config
│   │   ├── tool_docs.yaml
│   │   ├── business_context.yaml
│   │   └── examples.yaml
│   └── routing/              # (NEW) Routing config
│       ├── keyword_map.yaml
│       └── synonyms.yaml
│
├── src/
│   ├── server.py             # (modified) Add routing integration
│   ├── kledo_client.py       # (unchanged)
│   ├── auth.py               # (unchanged)
│   ├── cache.py              # (unchanged)
│   ├── entities/             # (NEW) Entity registry module
│   │   ├── __init__.py
│   │   ├── schema.py         # Pydantic models for entities
│   │   ├── loader.py         # YAML entity loader
│   │   └── registry.py       # Entity registry class
│   ├── docs/                 # (NEW) Documentation module
│   │   ├── __init__.py
│   │   ├── enricher.py       # Tool enrichment
│   │   └── context.py        # Business context provider
│   ├── routing/              # (NEW) Routing module
│   │   ├── __init__.py
│   │   ├── keywords.py       # Keyword extraction
│   │   ├── resolver.py       # Intent resolution
│   │   └── suggester.py      # Tool suggestions
│   ├── tools/                # (existing, modified)
│   │   ├── __init__.py       # Add enrichment wrapper
│   │   ├── financial.py      # (modified) Use entity context
│   │   ├── invoices.py       # (modified) Use entity context
│   │   └── ...
│   └── utils/                # (existing)
│       ├── helpers.py
│       └── logger.py
│
└── docs/                     # (NEW) Generated documentation
    ├── ENTITIES.md           # Entity relationship docs
    ├── TOOLS.md              # Tool catalog
    └── diagrams/             # ERD and flow diagrams
```

---

## Component Details

### 1. Entity Registry

**Purpose:** Central source of truth for all Kledo API entities.

**Schema format (YAML):**

```yaml
# config/entities/invoice.yaml
entity: invoice
display_name: "Sales Invoice"
api_endpoints:
  list: /finance/invoices
  detail: /finance/invoices/{id}
  totals: /finance/invoices/totals

fields:
  id:
    type: integer
    description: "Unique invoice identifier"
    api_field: id
  trans_number:
    type: string
    description: "Invoice number (e.g., INV-0001)"
    api_field: trans_number
    searchable: true
  contact_id:
    type: integer
    description: "Customer ID"
    api_field: contact_id
    relation: contact
  grand_total:
    type: decimal
    description: "Total invoice amount including tax"
    api_field: grand_total
  status_id:
    type: integer
    description: "Invoice status"
    api_field: status_id
    enum:
      1: Draft
      2: Pending
      3: Paid
      4: Overdue
      5: Cancelled

relationships:
  - type: belongs_to
    entity: contact
    foreign_key: contact_id
    description: "Customer who received the invoice"
  - type: has_many
    entity: invoice_item
    foreign_key: invoice_id
    description: "Line items on the invoice"

business_terms:
  - "faktur"
  - "tagihan"
  - "piutang"
```

**Registry class:**

```python
# src/entities/registry.py
class EntityRegistry:
    def __init__(self, config_path: str):
        self._entities: Dict[str, EntityDefinition] = {}
        self._load_entities(config_path)

    def get_entity(self, name: str) -> EntityDefinition:
        """Get entity definition by name."""
        return self._entities.get(name)

    def get_relationships(self, entity: str) -> List[Relationship]:
        """Get all relationships for an entity."""
        ...

    def get_fields(self, entity: str) -> List[FieldDefinition]:
        """Get all fields for an entity."""
        ...

    def find_by_business_term(self, term: str) -> Optional[str]:
        """Find entity by Indonesian/business term."""
        ...
```

### 2. Documentation Layer

**Purpose:** Enrich tool descriptions with examples, context, and business terminology.

**Enrichment process:**

```python
# src/docs/enricher.py
class ToolEnricher:
    def __init__(self, entity_registry: EntityRegistry, docs_config: str):
        self.registry = entity_registry
        self._load_docs(docs_config)

    def enrich_tool(self, tool: Tool) -> Tool:
        """Add rich context to tool definition."""
        # Get base documentation
        docs = self._tool_docs.get(tool.name, {})

        # Build enhanced description
        enhanced_desc = self._build_description(tool, docs)

        # Add examples to schema
        enhanced_schema = self._add_examples(tool.inputSchema, docs)

        return Tool(
            name=tool.name,
            description=enhanced_desc,
            inputSchema=enhanced_schema
        )

    def _build_description(self, tool: Tool, docs: dict) -> str:
        """Build rich description with context."""
        parts = [tool.description]

        # Add business context
        if docs.get("business_context"):
            parts.append(f"\n\nBusiness context: {docs['business_context']}")

        # Add example queries
        if docs.get("example_queries"):
            parts.append("\n\nExample queries:")
            for q in docs["example_queries"]:
                parts.append(f"- \"{q}\"")

        # Add related entities
        if docs.get("entities"):
            parts.append(f"\n\nRelated entities: {', '.join(docs['entities'])}")

        return "\n".join(parts)
```

**Documentation config:**

```yaml
# config/docs/tool_docs.yaml
invoice_list_sales:
  business_context: |
    Sales invoices represent money owed to your company by customers.
    In Indonesian accounting, this is "faktur penjualan" or "piutang usaha".
  example_queries:
    - "Show me unpaid invoices"
    - "List invoices from last month"
    - "Find invoices for customer ABC"
    - "Tagihan yang belum dibayar"
  entities:
    - invoice
    - contact
  tips:
    - Use status_id=2 for pending/unpaid invoices
    - Use date_from with last_month for quick filtering
```

### 3. Routing Layer

**Purpose:** Map business terms and natural language to appropriate tools.

**Design principle:** Simple keyword matching, not ML/embeddings. Per PROJECT.md, semantic search with vectors is overkill for ~30 tools.

```python
# src/routing/resolver.py
class IntentResolver:
    def __init__(self, keyword_map: str, synonyms: str):
        self._load_mappings(keyword_map, synonyms)

    def resolve(self, query: str) -> ToolSuggestion:
        """Resolve natural language query to tool suggestion."""
        # Normalize query
        normalized = self._normalize(query)

        # Extract keywords
        keywords = self._extract_keywords(normalized)

        # Match against keyword map
        matches = self._match_keywords(keywords)

        # Return best match with confidence
        return ToolSuggestion(
            tool_name=matches[0].tool if matches else None,
            confidence=matches[0].score if matches else 0,
            inferred_params=self._infer_params(query, matches[0]) if matches else {}
        )

    def _normalize(self, query: str) -> str:
        """Normalize query (lowercase, remove punctuation, expand synonyms)."""
        ...

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract significant keywords from query."""
        ...

    def _match_keywords(self, keywords: List[str]) -> List[Match]:
        """Match keywords against tool mappings."""
        ...
```

**Keyword mapping config:**

```yaml
# config/routing/keyword_map.yaml
invoice_list_sales:
  keywords:
    - invoice
    - invoices
    - faktur
    - tagihan
    - piutang
    - receivable
    - ar
  modifiers:
    unpaid: { status_id: 2 }
    pending: { status_id: 2 }
    paid: { status_id: 3 }
    overdue: { status_id: 4 }
    belum_dibayar: { status_id: 2 }

financial_bank_balances:
  keywords:
    - bank
    - balance
    - saldo
    - kas
    - cash
  priority: high  # Always suggest if "bank" mentioned

contact_list:
  keywords:
    - customer
    - pelanggan
    - vendor
    - supplier
    - contact
    - kontak
  modifiers:
    customer: { type_id: 1 }
    pelanggan: { type_id: 1 }
    vendor: { type_id: 2 }
    supplier: { type_id: 2 }
```

---

## Anti-Patterns to Avoid

### 1. Over-Engineering the Router

**Wrong:** Build ML-based semantic search with embeddings
**Right:** Simple keyword matching with synonym expansion

The project has ~30 tools. Vector search adds complexity without proportional value. The keyword approach is:
- Transparent (easy to debug)
- Maintainable (edit YAML to add terms)
- Fast (no model inference)

### 2. Duplicating Entity Information

**Wrong:** Define entity fields in tool handlers AND entity registry
**Right:** Single source of truth in entity registry, tools import

```python
# WRONG - duplicated
async def _list_invoices(args, client):
    # Fields defined here AND in entity YAML
    status_map = {1: "Draft", 2: "Pending", 3: "Paid"}
    ...

# RIGHT - single source
async def _list_invoices(args, client):
    entity = registry.get_entity("invoice")
    status_map = entity.get_field("status_id").enum
    ...
```

### 3. Tight Coupling Between Layers

**Wrong:** Documentation layer directly modifies tool handlers
**Right:** Documentation layer wraps/enriches at server level

```python
# WRONG - tight coupling
# In invoices.py
from src.docs import get_invoice_docs
def get_tools():
    docs = get_invoice_docs()  # Coupling!
    return [Tool(description=docs["invoice_list"]...)]

# RIGHT - loose coupling
# In server.py
def list_tools():
    base_tools = invoices.get_tools()
    return [enricher.enrich(t) for t in base_tools]
```

---

## Scalability Considerations

| Concern | Current (~30 tools) | Future (~100 tools) | Recommendation |
|---------|---------------------|---------------------|----------------|
| Tool lookup | O(n) list scan | May slow down | Add index by category |
| Keyword matching | Simple string match | Could get noisy | Consider tool categories |
| Entity loading | Load all at startup | Memory increase | Lazy loading option |
| Documentation | All in one file | Hard to maintain | Split by domain |

For the current scope (30-50 tools), simple approaches work. Build in hooks for optimization later:

```python
# src/entities/registry.py
class EntityRegistry:
    def __init__(self, lazy_load: bool = False):
        self._lazy = lazy_load
        if not lazy_load:
            self._load_all()

    def get_entity(self, name: str) -> EntityDefinition:
        if self._lazy and name not in self._entities:
            self._load_entity(name)
        return self._entities.get(name)
```

---

## Sources and Confidence

### HIGH Confidence (Official/Authoritative)

- [MCP Architecture Overview](https://modelcontextprotocol.io/docs/learn/architecture) - Official MCP documentation
- [MCP Tools Specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) - Official tool definition spec
- Existing codebase analysis (server.py, kledo_client.py, tool modules)

### MEDIUM Confidence (Verified Patterns)

- [MCP Registry Architecture](https://workos.com/blog/mcp-registry-architecture-technical-overview) - Federation and discovery patterns
- [Multi-Agent MCP Design](https://medium.com/@personal.gautamgiri/designing-multi-agent-mcp-servers-with-shared-tools-and-resources-part-1-63fd809694c7) - Shared tool registry pattern
- [API Design Best Practices](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design) - Entity mapping layer patterns
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.0) - Self-describing schema patterns

### Project-Specific Context

- PROJECT.md - Confirms simple routing over semantic search
- API_MAPPING.md - Documents existing 40 of 323 endpoints
- ARCHITECTURE.md - Existing architecture documentation

---

## Summary

### Components to Build

1. **Entity Registry** (Phase 1)
   - YAML-based entity definitions
   - Relationship mapping
   - Field catalog with types and enums

2. **Documentation Layer** (Phase 2)
   - Tool enrichment system
   - Business context provider
   - Example generator

3. **Routing Layer** (Phase 3)
   - Keyword extraction
   - Intent resolution
   - Tool suggestion

### Key Integration Points

- Entity Registry: Standalone, imported by tools and docs
- Documentation: Wraps tools at server level in `list_tools()`
- Routing: Hooks into server before `call_tool()`

### Build Dependencies

```
Entity Registry (no dependencies)
    |
    v
Documentation Layer (depends on Entity Registry)
    |
    v
Routing Layer (depends on Entity Registry + Documentation for context)
```

### Files to Create

| Phase | New Files | Modified Files |
|-------|-----------|----------------|
| 1 | `src/entities/*`, `config/entities/*` | None |
| 2 | `src/docs/*`, `config/docs/*` | `src/tools/__init__.py` |
| 3 | `src/routing/*`, `config/routing/*` | `src/server.py` |

---

**Research completed:** 2026-01-21
**Ready for:** Roadmap creation
