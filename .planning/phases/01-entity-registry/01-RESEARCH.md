# Phase 1: Entity Registry - Research

**Researched:** 2026-01-21
**Domain:** YAML Entity Schema Design, Python YAML Validation, ERD Generation
**Confidence:** HIGH

## Summary

This research investigates the technical domain for creating a machine-readable entity registry for Kledo API entities. The existing codebase already contains an OpenAPI 3.0 spec (`api-1.yaml`, ~900KB) with comprehensive schema definitions that can serve as a reference for entity extraction. The tool modules (`src/tools/*.py`) demonstrate the actual field usage patterns for Invoice, Contact, Product, Order, Delivery, and Financial entities.

The recommended approach uses **Pydantic models as the primary schema definition** with YAML as a human-readable configuration layer. This aligns with the existing codebase architecture (Pydantic already used for MCP types) and provides native JSON Schema generation, type validation, and ERD diagram support via `erdantic`. The entity definitions should follow OpenAPI/JSON Schema conventions as specified in CONTEXT.md, enabling future integration with documentation generation.

**Primary recommendation:** Define entities as Pydantic models in `src/entities/`, generate YAML exports for human review, and use erdantic for ERD visualization. Validation happens at Python runtime via Pydantic rather than external JSON Schema validators.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.10+ | Entity model definition with JSON Schema generation | Already in codebase, native MCP integration, erdantic support |
| pydantic-yaml | 1.6.0 | YAML serialization for Pydantic models | Supports Pydantic V2, simple `to_yaml_str()` and `parse_yaml_raw_as()` |
| PyYAML | 6.0+ | YAML parsing (already in codebase) | Already used for `endpoints.yaml` loading |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| erdantic | 1.2.0 | ERD diagram generation from Pydantic models | Generate visual entity relationship diagrams (ENTY-03) |
| graphviz | 0.20+ | Graph rendering (erdantic dependency) | Required for erdantic PNG/SVG output |
| ruamel.yaml | 0.18+ | Round-trip YAML with comments | Only if preserving YAML comments is needed (optional) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic models | Raw YAML + JSON Schema validator | Loses Python integration, requires separate validation step |
| erdantic | LinkML | More powerful but complex, overkill for 7-10 entities |
| PyYAML | strictyaml | Safer validation but steeper learning curve, less ecosystem support |
| PyYAML | ruamel.yaml | Better comment preservation but more complex API |

**Installation:**
```bash
pip install pydantic-yaml erdantic graphviz
```

Note: `graphviz` Python package requires the Graphviz system binary. Install with:
- macOS: `brew install graphviz`
- Ubuntu: `apt-get install graphviz`
- Windows: Download from graphviz.org

## Architecture Patterns

### Recommended Project Structure
```
src/
├── entities/
│   ├── __init__.py           # Exports load_entity(), get_all_entities()
│   ├── loader.py             # YAML loading and Pydantic validation
│   ├── models/
│   │   ├── __init__.py       # Re-exports all entity models
│   │   ├── base.py           # Base entity model with common fields
│   │   ├── invoice.py        # Invoice, InvoiceItem models
│   │   ├── contact.py        # Contact, ContactGroup models
│   │   ├── product.py        # Product, ProductCategory models
│   │   ├── order.py          # Order, OrderItem models
│   │   ├── delivery.py       # Delivery, DeliveryItem models
│   │   ├── account.py        # Account, BankAccount models
│   │   └── bank.py           # BankTransaction models
│   └── schemas/
│       ├── invoice.yaml      # Human-readable YAML (generated from models)
│       ├── contact.yaml
│       ├── product.yaml
│       └── ...
├── tools/                    # Existing tool modules (unchanged)
└── ...
```

### Pattern 1: Pydantic Model with Rich Metadata
**What:** Define entities as Pydantic models with `Field()` metadata for descriptions, examples, and business meaning.
**When to use:** All entity definitions - provides type safety, JSON Schema generation, and documentation.
**Example:**
```python
# Source: Pydantic V2 Field documentation
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal

class InvoiceItem(BaseModel):
    """Line item within an invoice."""

    product_id: int = Field(
        description="Reference to the product being invoiced",
        examples=[1234],
        json_schema_extra={"api_name": "product_id", "business_meaning": "Links to Product entity"}
    )
    desc: str = Field(
        description="Product description or custom line item description",
        examples=["Widget Pro - Blue"],
        json_schema_extra={"api_name": "desc"}
    )
    qty: Decimal = Field(
        description="Quantity ordered",
        examples=[10.0],
        ge=0
    )
    price: Decimal = Field(
        description="Unit price before tax",
        examples=[150000.00],
        ge=0
    )
    amount: Decimal = Field(
        description="Line total (qty * price)",
        examples=[1500000.00]
    )

class Invoice(BaseModel):
    """Sales invoice representing a transaction with a customer."""

    id: int = Field(description="Unique invoice identifier")
    trans_number: str = Field(
        description="Invoice number displayed to users",
        examples=["INV-2026-0001"],
        json_schema_extra={"api_name": "trans_number"}
    )
    trans_date: date = Field(
        description="Invoice date",
        examples=["2026-01-21"]
    )
    due_date: Optional[date] = Field(
        default=None,
        description="Payment due date"
    )
    contact_id: int = Field(
        description="Customer/contact reference",
        json_schema_extra={"relationship": "Contact", "cardinality": "many-to-one"}
    )
    contact_name: Optional[str] = Field(
        default=None,
        description="Denormalized customer name for display"
    )
    status_id: int = Field(
        description="Invoice status (1=Draft, 2=Pending, 3=Paid)",
        json_schema_extra={"enum_source": "init.finance.invoice_status"}
    )
    status_name: Optional[str] = Field(
        default=None,
        description="Denormalized status name"
    )
    subtotal: Decimal = Field(default=0, description="Sum of line items before tax")
    tax_amount: Decimal = Field(default=0, description="Total tax amount")
    grand_total: Decimal = Field(default=0, description="Total including tax")
    amount_paid: Decimal = Field(default=0, description="Amount already paid")
    detail: list[InvoiceItem] = Field(
        default_factory=list,
        description="Line items",
        json_schema_extra={"relationship": "InvoiceItem", "cardinality": "one-to-many"}
    )
    memo: Optional[str] = Field(default=None, description="Internal notes")
```

### Pattern 2: YAML Export for Human Review
**What:** Generate YAML from Pydantic models for documentation and human review.
**When to use:** When users need to review/modify entity definitions without touching Python.
**Example:**
```python
# Source: pydantic-yaml documentation
from pydantic_yaml import to_yaml_str

# Generate YAML from model schema
schema = Invoice.model_json_schema()
yaml_output = to_yaml_str(schema)

# Or use custom YAML generation for cleaner output
import yaml

def export_entity_yaml(model_class) -> str:
    """Export Pydantic model to clean YAML format."""
    schema = model_class.model_json_schema()
    return yaml.dump(schema, default_flow_style=False, sort_keys=False)
```

### Pattern 3: Entity Loader with Validation
**What:** Load YAML files and validate against Pydantic models.
**When to use:** Runtime validation of entity configurations.
**Example:**
```python
# Source: Pydantic model_validate pattern
from pathlib import Path
from typing import Type, TypeVar
import yaml
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

def load_entity(entity_name: str, model_class: Type[T]) -> T:
    """Load entity definition from YAML and validate."""
    yaml_path = Path(__file__).parent / "schemas" / f"{entity_name}.yaml"

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    return model_class.model_validate(data)

def get_all_entities() -> dict[str, BaseModel]:
    """Load all entity definitions."""
    from .models import Invoice, Contact, Product, Order, Delivery, Account, Bank

    entities = {
        "invoice": Invoice,
        "contact": Contact,
        "product": Product,
        "order": Order,
        "delivery": Delivery,
        "account": Account,
        "bank": Bank
    }

    return {name: load_entity(name, model) for name, model in entities.items()}
```

### Pattern 4: Relationship Modeling
**What:** Use `json_schema_extra` to encode relationships for ERD generation.
**When to use:** When defining foreign key relationships between entities.
**Example:**
```python
class Invoice(BaseModel):
    contact_id: int = Field(
        description="Customer/contact reference",
        json_schema_extra={
            "relationship": {
                "target": "Contact",
                "type": "many-to-one",
                "foreign_key": "id"
            }
        }
    )
    detail: list[InvoiceItem] = Field(
        json_schema_extra={
            "relationship": {
                "target": "InvoiceItem",
                "type": "one-to-many",
                "embedded": True  # Items are embedded, not separate entity
            }
        }
    )
```

### Anti-Patterns to Avoid
- **Duplicating API response structure exactly:** API responses have flattened denormalized fields (e.g., `contact_name` alongside `contact_id`). Model the normalized entity structure with explicit relationship metadata, not the API response shape.
- **Using raw dicts instead of Pydantic models:** Loses type safety, IDE support, and erdantic compatibility.
- **Storing examples as separate files:** Examples belong in `Field(examples=[...])` for co-location with field definitions.
- **Over-engineering relationship metadata:** Start with simple `"relationship": "Entity"` strings; only add cardinality/foreign_key details if ERD generator needs them.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON Schema generation | Custom dict builder | `model.model_json_schema()` | Pydantic handles all edge cases, JSON Schema compliance |
| YAML parsing | Custom parser | `yaml.safe_load()` | Security-tested, handles all YAML edge cases |
| ERD diagrams | Custom GraphViz DOT generation | `erdantic.create(Model).draw()` | Handles complex inheritance, multiple output formats |
| Type validation | `isinstance()` checks | Pydantic validators | Comprehensive validation with clear error messages |
| Field metadata | Custom annotations | `Field(json_schema_extra={...})` | Standard Pydantic pattern, survives schema generation |

**Key insight:** Pydantic V2's `model_json_schema()` and `Field()` metadata handle 95% of entity definition needs. The remaining 5% (relationship visualization) is handled by erdantic. Don't build custom schema generators.

## Common Pitfalls

### Pitfall 1: YAML Boolean Gotchas (Norway Problem)
**What goes wrong:** YAML 1.1 interprets `yes`, `no`, `on`, `off`, `NO` as booleans, causing data corruption.
**Why it happens:** PyYAML defaults to YAML 1.1 which has loose boolean parsing.
**How to avoid:** Always use `yaml.safe_load()`, quote string values that look like booleans in YAML files, prefer explicit `true`/`false` for booleans.
**Warning signs:** Status values like "NO" getting converted to `False`.

### Pitfall 2: Circular Import with Entity Models
**What goes wrong:** `Invoice` references `Contact`, `Contact` references `Invoice` for receivables - circular import.
**Why it happens:** Python modules importing each other at definition time.
**How to avoid:** Use string forward references (`"Contact"` instead of `Contact`) in type hints, or consolidate related models in same file.
**Warning signs:** `ImportError` or `NameError` during import.

### Pitfall 3: API Field Names vs Model Field Names
**What goes wrong:** Kledo API uses `trans_number`, `trans_date` but you might want `invoice_number`, `invoice_date` in models.
**Why it happens:** API field names are database-driven, not semantic.
**How to avoid:** Keep API field names in models but document the semantic meaning. Use `json_schema_extra={"api_name": "trans_number", "display_name": "Invoice Number"}` for mapping.
**Warning signs:** Field name mismatches when validating API responses against models.

### Pitfall 4: Decimal vs Float for Currency
**What goes wrong:** Using `float` for currency fields causes precision errors (0.1 + 0.2 != 0.3).
**Why it happens:** IEEE 754 floating point representation.
**How to avoid:** Use `Decimal` type for all monetary fields, or `int` representing cents/smallest currency unit.
**Warning signs:** Rounding errors in totals, subtotals not adding up.

### Pitfall 5: Missing Graphviz System Binary
**What goes wrong:** `erdantic.create().draw()` fails with "Graphviz executables not found".
**Why it happens:** Python `graphviz` package is just a wrapper; needs actual Graphviz installed.
**How to avoid:** Document Graphviz installation in setup instructions, add check in ERD generation code.
**Warning signs:** `ExecutableNotFound: failed to execute 'dot'` error.

## Code Examples

Verified patterns from official sources:

### Pydantic Model to JSON Schema
```python
# Source: https://docs.pydantic.dev/latest/concepts/json_schema/
from pydantic import BaseModel, Field

class Contact(BaseModel):
    id: int
    name: str = Field(description="Contact's full name")
    type_id: int = Field(description="1=Customer, 2=Vendor, 3=Both")

# Generate JSON Schema
schema = Contact.model_json_schema()
# Returns: {'properties': {'id': {'title': 'Id', 'type': 'integer'}, ...}, 'required': ['id', 'name', 'type_id'], ...}
```

### YAML Serialization with pydantic-yaml
```python
# Source: https://pypi.org/project/pydantic-yaml/
from pydantic_yaml import to_yaml_str, parse_yaml_raw_as

# Serialize to YAML
yaml_str = to_yaml_str(contact_instance)

# Parse YAML to model
contact = parse_yaml_raw_as(Contact, yaml_string)
```

### ERD Generation with erdantic
```python
# Source: https://github.com/drivendataorg/erdantic
import erdantic as erd
from src.entities.models import Invoice, Contact, Product

# Create diagram from multiple models
diagram = erd.create(Invoice, Contact, Product)

# Save as PNG (requires Graphviz binary)
diagram.draw("docs/erd.png")

# Or get DOT source for custom rendering
dot_source = diagram.to_dot()
```

### Safe YAML Loading
```python
# Source: PyYAML documentation
import yaml
from pathlib import Path

def load_yaml_safe(filepath: Path) -> dict:
    """Load YAML file safely - only basic types, no arbitrary code execution."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic V1 `.schema()` | Pydantic V2 `.model_json_schema()` | Pydantic 2.0 (2023) | Different method name, richer schema output |
| Manual YAML schema files | Pydantic models with YAML export | Current recommendation | Single source of truth in Python code |
| Custom ERD scripts | erdantic library | v1.0 (2023) | Native Pydantic V2 support |
| JSON Schema Draft-04/07 | Draft 2020-12 | 2020 | Pydantic V2 outputs 2020-12 compliant schemas |

**Deprecated/outdated:**
- `YamlModel` base class from pydantic-yaml v0.x: Removed in v1.0, use `to_yaml_str()` function instead
- Pydantic V1 `schema()` method: Use V2 `model_json_schema()` instead
- erdantic D2 output: Graphviz preferred, D2 is secondary format

## Open Questions

Things that couldn't be fully resolved:

1. **ERD in this phase vs Phase 2?**
   - What we know: CONTEXT.md lists ERD generation under Claude's discretion
   - What's unclear: Whether to generate ERD as part of entity definition (Phase 1) or documentation (Phase 2)
   - Recommendation: Include basic ERD generation in Phase 1 (satisfies ENTY-03), defer MkDocs integration to Phase 2

2. **YAML schema files - generate or author?**
   - What we know: CONTEXT.md says "YAML format" for entity definitions
   - What's unclear: Whether YAML is primary source or generated from Python models
   - Recommendation: Python Pydantic models are primary source, YAML files are generated for human review

3. **Kledo API entity coverage completeness**
   - What we know: OpenAPI spec has ~50+ schemas, tools use ~7 core entities
   - What's unclear: Which entities are required for "complete" registry
   - Recommendation: Start with 7 core entities used by existing tools (Invoice, Contact, Product, Order, Delivery, Account, Bank), extend on demand

4. **Real API response examples**
   - What we know: CONTEXT.md mentions user will provide real invoice data
   - What's unclear: When this data will be available
   - Recommendation: Use placeholder examples initially, update with real data when provided

## Sources

### Primary (HIGH confidence)
- [Pydantic JSON Schema Documentation](https://docs.pydantic.dev/latest/concepts/json_schema/) - JSON Schema generation, Field metadata
- [erdantic GitHub](https://github.com/drivendataorg/erdantic) - v1.2.0 (Sep 2025), Pydantic V2 support confirmed
- [pydantic-yaml PyPI](https://pypi.org/project/pydantic-yaml/) - v1.6.0 (Aug 2025), Pydantic V2 support
- Existing codebase: `api-1.yaml` OpenAPI spec with entity schemas, `src/tools/*.py` field usage patterns

### Secondary (MEDIUM confidence)
- [OpenAPI Specification v3.1](https://spec.openapis.org/oas/v3.1.0.html) - JSON Schema alignment for entity format conventions
- [Speakeasy Data Types Best Practices](https://www.speakeasy.com/openapi/schemas) - Schema design patterns
- [ruamel.yaml PyPI](https://pypi.org/project/ruamel.yaml/) - YAML 1.2 support, round-trip comparison

### Tertiary (LOW confidence)
- [StrictYAML](https://hitchdev.com/strictyaml/) - Alternative YAML parser (not recommended due to ecosystem size)
- [LinkML ER Diagrams](https://linkml.io/linkml/generators/erdiagram.html) - Alternative ERD approach (more complex than needed)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Pydantic and erdantic are well-documented, already partially in codebase
- Architecture: HIGH - Follows existing codebase patterns, clear extension points
- Pitfalls: HIGH - YAML/Python gotchas well-documented, Graphviz dependency explicit

**Research date:** 2026-01-21
**Valid until:** 2026-03-21 (60 days - stable domain, no major releases expected)

---

*Phase: 01-entity-registry*
*Research completed: 2026-01-21*
