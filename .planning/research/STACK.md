# Stack Research: API Documentation and Entity Mapping for MCP Server

**Project:** Kledo API MCP Server - Documentation Enhancement
**Researched:** 2026-01-21
**Research Mode:** Stack (Technology Recommendations)

---

## Executive Summary

This research addresses the stack requirements for adding comprehensive API documentation, entity relationship mapping, and smart tool routing to the existing Kledo MCP server. The project already uses Python with MCP SDK, Pydantic, and YAML configuration. The recommended approach leverages these existing foundations while adding focused tools for documentation generation and diagram creation.

**Key Finding:** The existing architecture is well-suited for enhancement. The endpoint YAML configuration and Pydantic-based tool definitions provide natural extension points for richer documentation without requiring architectural changes.

---

## Recommended Stack

### Core Framework (Existing - No Changes)

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| MCP SDK | >=1.25.0 | MCP server implementation | Already in use; current version supports structured output and enhanced tool annotations |
| Pydantic | >=2.0.0 | Data validation and models | Already in use; provides Field metadata for tool descriptions |
| httpx | >=0.25.0 | Async HTTP client | Already in use; no changes needed |
| PyYAML | >=6.0.0 | Configuration parsing | Already in use for endpoints.yaml |

**Confidence:** HIGH - Verified from existing requirements.txt

### Documentation Generation

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| MkDocs | >=1.6.0 | Static site generator | Simpler than Sphinx, Markdown-native, excellent for API docs |
| mkdocs-material | >=9.7.1 | MkDocs theme | Industry standard theme; clean navigation, search, mobile support |
| mkdocstrings[python] | >=2.0.1 | Auto-doc from docstrings | Generates API reference from Python docstrings automatically |

**Confidence:** HIGH - Versions verified via PyPI (Dec 2025 releases)

**Why MkDocs over Sphinx:**
- Lower learning curve for Markdown-based content
- Material theme provides modern, clean documentation UI
- mkdocstrings provides equivalent auto-documentation capability
- Better suited for API reference documentation that will be read by both humans and AI tools
- Faster build times for iterative documentation development

### Diagram Generation

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| erdantic | >=1.2.0 | ERD from Pydantic models | Directly supports Pydantic V2; generates Graphviz or Mermaid output |
| mermaid-py | >=0.8.1 | Programmatic Mermaid diagrams | Python interface to Mermaid.js; embeds in Markdown |
| Graphviz | system | Graph rendering backend | Required by erdantic; available via conda or system package |

**Confidence:** HIGH - erdantic v1.2.0 (Sep 2025), mermaid-py v0.8.1 (Dec 2025) verified via GitHub/PyPI

**Why erdantic:**
- Native Pydantic V2 support (matches project's existing Pydantic usage)
- Also supports dataclasses, attrs, msgspec for future flexibility
- Outputs both Graphviz (PNG/SVG) and Mermaid (embedded in docs)
- Terminal node option allows splitting large diagrams

**Why Mermaid for embedded diagrams:**
- Native GitHub/GitLab rendering support
- Embeds directly in Markdown documentation
- No external image hosting required
- Human-readable text format for version control

### Tool Enhancement (Native MCP Patterns)

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| Pydantic Field | (bundled) | Rich tool descriptions | Use `description`, `title`, `examples` in Field() for tool metadata |
| typing.Annotated | (stdlib) | Type-level metadata | Combine type hints with Field metadata per Pydantic best practices |
| Jinja2 | >=3.1.0 | Template-based doc generation | Generate consistent tool documentation from YAML/Python definitions |

**Confidence:** HIGH - Native Python/Pydantic patterns; Jinja2 is mature

### Keyword-Based Routing (Simple Approach)

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| Built-in dict/set | (stdlib) | Keyword mapping | Simple keyword-to-tool lookup; no vector DB overhead |
| difflib | (stdlib) | Fuzzy matching | SequenceMatcher for typo-tolerant routing; no dependencies |
| rapidfuzz (optional) | >=3.0.0 | Fast fuzzy matching | Drop-in difflib replacement if performance needed |

**Confidence:** HIGH - Standard library approach; rapidfuzz is well-maintained

**Why NOT vector search:**
- Overkill for ~30-50 tools with well-defined keywords
- Adds embedding model dependency and latency
- Simple keyword matching with fuzzy fallback is sufficient
- MCP protocol already provides tool discovery; routing augments, doesn't replace

---

## Documentation Generation Details

### Approach: Embedded + Static Docs

1. **Embedded Tool Descriptions** (in code)
   - Rich docstrings in tool handler functions
   - Pydantic Field descriptions for parameters
   - Examples in inputSchema

2. **Static Documentation** (generated)
   - API endpoint catalog from endpoints.yaml
   - Entity relationship diagrams from Pydantic models
   - Tool reference pages from docstrings via mkdocstrings

### File Structure

```
docs/
  index.md              # Overview
  api/
    endpoints.md        # Auto-generated endpoint catalog
    entities.md         # ERD diagrams and entity descriptions
  tools/
    financial.md        # Tool reference by category
    invoices.md
    contacts.md
    ...
  guides/
    workflows.md        # Common use patterns
mkdocs.yml              # MkDocs configuration
```

### Generation Scripts

```python
# scripts/generate_docs.py
# - Parse endpoints.yaml -> Markdown endpoint catalog
# - Run erdantic on Pydantic models -> Mermaid ERD
# - Jinja2 templates for consistent formatting
```

---

## Tool Enhancement Patterns

### Current Tool Definition (from codebase)

```python
Tool(
    name="contact_list",
    description="List customers and vendors with optional search and filtering.",
    inputSchema={...}
)
```

### Enhanced Tool Definition Pattern

```python
from typing import Annotated
from pydantic import Field

# Option 1: Richer descriptions in existing Tool() format
Tool(
    name="contact_list",
    description="""List customers and vendors with optional search and filtering.

    Use cases:
    - Find customer by name or email
    - Get all vendors for a product category
    - Search contacts for reporting

    Related tools: contact_get_detail, invoice_list (filter by contact)
    Related entities: Contact, ContactGroup
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "search": {
                "type": "string",
                "description": "Search by name, email, phone, or company. Supports partial matching."
            },
            ...
        }
    }
)

# Option 2: Pydantic model for input validation (if migrating to FastMCP pattern)
class ContactListInput(BaseModel):
    search: Annotated[str | None, Field(
        default=None,
        description="Search by name, email, phone, or company. Supports partial matching.",
        examples=["john@example.com", "Acme Corp"]
    )]
    type_id: Annotated[int | None, Field(
        default=None,
        description="Filter by contact type: 1=Customer, 2=Vendor, 3=Both"
    )]
```

**Recommendation:** Start with Option 1 (enhanced descriptions in existing format) since the codebase already uses direct Tool() definitions. Option 2 (Pydantic input models) can be adopted later if migrating to FastMCP decorators.

---

## Keyword Routing Implementation

### Simple Keyword Mapping

```python
# config/tool_keywords.yaml
tools:
  contact_list:
    keywords: [customer, vendor, contact, client, supplier, CRM]
    aliases: [find customer, search contacts, list clients]

  invoice_list:
    keywords: [invoice, bill, sale, revenue, receivable]
    aliases: [find invoice, sales list, unpaid invoices]

  financial_sales_summary:
    keywords: [sales, revenue, income, report, summary, total]
    aliases: [sales report, revenue summary, how much sold]
```

### Routing Logic

```python
from difflib import SequenceMatcher

def find_best_tool(query: str, tool_keywords: dict) -> str | None:
    query_lower = query.lower()

    # Exact keyword match
    for tool_name, config in tool_keywords.items():
        if any(kw in query_lower for kw in config['keywords']):
            return tool_name

    # Fuzzy alias match
    best_match = None
    best_ratio = 0.6  # minimum threshold

    for tool_name, config in tool_keywords.items():
        for alias in config.get('aliases', []):
            ratio = SequenceMatcher(None, query_lower, alias.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = tool_name

    return best_match
```

**Note:** This routing is optional/supplementary. MCP clients (like Claude) already perform tool selection based on descriptions. This routing helps with:
- Programmatic tool selection in automation scripts
- Suggesting relevant tools in response formatting
- Documentation cross-referencing

---

## Not Recommended

### Avoid These Technologies

| Technology | Why Avoid |
|------------|-----------|
| Sphinx | Steeper learning curve; reST is less accessible than Markdown; overkill for this project size |
| Vector databases (Pinecone, Weaviate, etc.) | Massive overkill for ~50 tools; adds infrastructure complexity |
| LangChain/LlamaIndex for routing | Heavy dependencies for simple keyword matching; unnecessary abstraction |
| Auto-generated OpenAPI specs | Project doesn't expose REST endpoints; MCP tools aren't OpenAPI-compatible |
| Database-backed documentation | Static Markdown is sufficient; no need for CMS complexity |

### Anti-Patterns to Avoid

| Anti-Pattern | Why Bad | Alternative |
|--------------|---------|-------------|
| Generating docs from external API exploration | Brittle; API changes break docs | Document from code as source of truth |
| Vector search for <100 tools | Latency overhead, embedding costs | Simple keyword matching |
| Separate documentation repository | Docs drift from code | Keep docs in same repo, generate from code |
| Over-documenting internal implementation | Noise for consumers | Focus on usage, inputs, outputs, examples |

---

## Confidence Levels

| Recommendation | Confidence | Verification Source |
|----------------|------------|---------------------|
| MkDocs + Material | HIGH | PyPI (9.7.1, Dec 2025); widely adopted |
| mkdocstrings | HIGH | PyPI (2.0.1, Dec 2025); used by FastAPI, Pydantic |
| erdantic | HIGH | GitHub/PyPI (1.2.0, Sep 2025); Pydantic V2 support confirmed |
| mermaid-py | HIGH | PyPI (0.8.1, Dec 2025); active development |
| Keyword routing approach | HIGH | Standard library; proven pattern |
| Pydantic Field metadata | HIGH | Official Pydantic docs; native pattern |
| MCP SDK 1.25.0 | HIGH | PyPI (Dec 2025); current stable |
| Avoid Sphinx | MEDIUM | Subjective; valid for larger projects but MkDocs fits better here |
| Avoid vector search | HIGH | Verified overkill for tool count; adds unnecessary complexity |

---

## Installation Commands

```bash
# Documentation generation
pip install mkdocs>=1.6.0 mkdocs-material>=9.7.1 "mkdocstrings[python]>=2.0.1"

# Diagram generation
pip install erdantic>=1.2.0 mermaid-py>=0.8.1
# Note: erdantic requires Graphviz system package
# macOS: brew install graphviz
# Ubuntu: apt-get install graphviz

# Optional: faster fuzzy matching
pip install rapidfuzz>=3.0.0

# Template generation
pip install Jinja2>=3.1.0
```

### Updated requirements.txt additions

```
# Documentation
mkdocs>=1.6.0
mkdocs-material>=9.7.1
mkdocstrings[python]>=2.0.1

# Diagrams
erdantic>=1.2.0
mermaid-py>=0.8.1

# Templates
Jinja2>=3.1.0

# Optional: faster fuzzy matching
# rapidfuzz>=3.0.0
```

---

## Sources

### Documentation Tools
- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) - Theme documentation
- [mkdocstrings](https://mkdocstrings.github.io/) - Auto-documentation plugin
- [mkdocstrings-python PyPI](https://pypi.org/project/mkdocstrings-python/) - Version verification

### Diagram Tools
- [erdantic GitHub](https://github.com/drivendataorg/erdantic) - ERD generation
- [erdantic documentation](https://erdantic.drivendata.org/stable/) - Usage examples
- [mermaid-py PyPI](https://pypi.org/project/mermaid-py/) - Python Mermaid interface
- [Mermaid ERD syntax](https://mermaid.js.org/syntax/entityRelationshipDiagram.html) - Diagram syntax

### MCP Best Practices
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) - Official tool spec
- [FastMCP Tools](https://gofastmcp.com/servers/tools) - Tool annotation patterns
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) - Official SDK

### Pydantic Patterns
- [Pydantic Fields](https://docs.pydantic.dev/latest/concepts/fields/) - Field metadata best practices
- [Pydantic Field Metadata](https://python.useinstructor.com/concepts/fields/) - LLM-oriented field usage
