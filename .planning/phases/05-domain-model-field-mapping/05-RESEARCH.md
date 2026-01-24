# Phase 5: Domain Model & Field Mapping - Research

**Researched:** 2026-01-24
**Domain:** Python domain modeling, data transformation, financial calculations
**Confidence:** HIGH

## Summary

This phase implements a domain model layer that converts confusing Kledo API field names to clear business terminology. The implementation uses Pydantic BaseModel (already a project dependency) with Decimal for financial precision, following the Data Mapper pattern.

Key findings:
- **Use Pydantic BaseModel** over dataclasses since pydantic is already a dependency and provides validation, serialization, and the existing entity models use it
- **Always initialize Decimal from strings** to avoid float precision errors in financial calculations
- **Validation at boundaries** - validate data integrity (net_sales + tax_collected = gross_sales) when converting from Kledo API

**Primary recommendation:** Create `InvoiceFinancials` as a Pydantic model with `model_validator` for data integrity checks, and a standalone mapper function in `kledo_mapper.py`.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | >=2.0.0 | Domain model definition | Already in project, provides validation + serialization |
| decimal (stdlib) | N/A | Financial precision | IEEE 854 compliance, exact decimal arithmetic |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=7.4.0 | Testing mappers | Already in dev dependencies |
| pytest-asyncio | >=0.21.0 | Async test support | Testing async tool functions |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic BaseModel | dataclasses | Pydantic already in project, provides validation; dataclasses require manual validation |
| Pydantic BaseModel | pydantic.dataclasses | Similar, but BaseModel is more consistent with existing entity models |
| Decimal | Integer cents | Simpler but requires conversion at display; Decimal more readable |

**Installation:**
No new packages needed - all dependencies already exist in pyproject.toml.

## Architecture Patterns

### Recommended Project Structure
```
src/
├── models/
│   ├── __init__.py          # Export domain models
│   └── invoice_financials.py # InvoiceFinancials domain model
├── mappers/                   # NEW directory
│   ├── __init__.py           # Export mapper functions
│   └── kledo_mapper.py       # from_kledo_invoice() function
├── tools/
│   ├── revenue.py            # UPDATE: use domain model
│   ├── invoices.py           # UPDATE: use domain model
│   └── sales_analytics.py    # UPDATE: use domain model
```

### Pattern 1: Pydantic Domain Model with Validation
**What:** Define domain model using Pydantic BaseModel with model_validator for data integrity
**When to use:** When converting external API data to internal domain representation
**Example:**
```python
# Source: Pydantic docs + project conventions
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator

class InvoiceFinancials(BaseModel):
    """Financial data for a single invoice with clear business terminology.

    Mapping from Kledo API:
    - net_sales = subtotal (revenue before tax)
    - tax_collected = total_tax (PPN)
    - gross_sales = amount_after_tax (total including tax)
    """
    net_sales: Decimal = Field(description="Revenue before tax (Penjualan Neto)")
    tax_collected: Decimal = Field(description="Tax collected (PPN)")
    gross_sales: Decimal = Field(description="Total including tax (Penjualan Bruto)")

    @model_validator(mode='after')
    def validate_financial_integrity(self) -> 'InvoiceFinancials':
        """Ensure net_sales + tax_collected = gross_sales (within tolerance)."""
        expected = self.net_sales + self.tax_collected
        tolerance = Decimal("0.01")  # 1 cent tolerance for rounding
        if abs(expected - self.gross_sales) > tolerance:
            raise ValueError(
                f"Financial integrity error: net_sales ({self.net_sales}) + "
                f"tax_collected ({self.tax_collected}) != gross_sales ({self.gross_sales})"
            )
        return self
```

### Pattern 2: Standalone Mapper Function
**What:** Separate function for converting Kledo API dict to domain model
**When to use:** Keep conversion logic isolated and testable
**Example:**
```python
# Source: Data Mapper pattern + Pydantic best practices
from decimal import Decimal
from typing import Any

from src.models.invoice_financials import InvoiceFinancials

def from_kledo_invoice(kledo_data: dict[str, Any]) -> InvoiceFinancials:
    """Convert Kledo invoice API response to domain model.

    Kledo API field mapping (PROVEN with real data):
    - subtotal = net_sales (base amount before tax)
    - total_tax = tax_collected (PPN)
    - amount_after_tax = gross_sales (subtotal + total_tax)

    Args:
        kledo_data: Raw invoice dict from Kledo API

    Returns:
        InvoiceFinancials domain model

    Raises:
        ValueError: If required fields missing or data integrity fails
        KeyError: If required fields are missing
    """
    # CRITICAL: Use str() to convert to Decimal, never from float directly
    return InvoiceFinancials(
        net_sales=Decimal(str(kledo_data["subtotal"])),
        tax_collected=Decimal(str(kledo_data["total_tax"])),
        gross_sales=Decimal(str(kledo_data["amount_after_tax"]))
    )
```

### Pattern 3: Batch Conversion with Error Handling
**What:** Convert list of invoices with graceful error handling
**When to use:** Processing multiple invoices from API response
**Example:**
```python
# Source: Production patterns for data pipelines
from typing import Any

def from_kledo_invoices(
    kledo_invoices: list[dict[str, Any]],
    skip_invalid: bool = False
) -> list[InvoiceFinancials]:
    """Convert list of Kledo invoices to domain models.

    Args:
        kledo_invoices: List of raw invoice dicts from API
        skip_invalid: If True, skip invalid invoices; if False, raise on first error

    Returns:
        List of InvoiceFinancials domain models
    """
    results = []
    for inv in kledo_invoices:
        try:
            results.append(from_kledo_invoice(inv))
        except (ValueError, KeyError) as e:
            if not skip_invalid:
                raise
            # Log and continue if skip_invalid=True
    return results
```

### Anti-Patterns to Avoid
- **Initializing Decimal from float:** `Decimal(data["subtotal"])` when subtotal is already float. Use `Decimal(str(data["subtotal"]))` always.
- **Validation in multiple places:** Validate once at the boundary (mapper), not in every tool.
- **Mixing raw Kledo fields with domain fields:** Either use raw dict OR domain model, never mix in same function.
- **Implicit conversions:** Always be explicit about type conversions, especially Decimal.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data validation | Manual if/else checks | Pydantic model_validator | Declarative, testable, automatic |
| JSON serialization | Manual dict building | Pydantic model_dump() | Handles Decimal, nested models |
| Field documentation | Comments everywhere | Pydantic Field(description=) | Self-documenting, schema export |
| Type coercion | Manual str() calls | Pydantic type validators | Consistent, handles edge cases |

**Key insight:** Pydantic already solves data transformation problems. The mapper function is minimal glue code, not a framework.

## Common Pitfalls

### Pitfall 1: Decimal from Float
**What goes wrong:** Initializing Decimal directly from float preserves float's imprecision
**Why it happens:** API response might have float values, natural to pass directly
**How to avoid:** Always convert to string first: `Decimal(str(value))`
**Warning signs:** Tests comparing Decimal values fail unexpectedly

### Pitfall 2: Missing Field Handling
**What goes wrong:** KeyError when Kledo API response missing expected field
**Why it happens:** API might return partial data, or field names change
**How to avoid:** Use `.get()` with defaults OR validate explicitly and raise clear error
**Warning signs:** Random KeyErrors in production

### Pitfall 3: Type Mismatch in Tools
**What goes wrong:** Tool still uses raw Kledo field names after domain model added
**Why it happens:** Partial migration, forgot to update
**How to avoid:** Update all usages together, grep for old field names
**Warning signs:** Mixed terminology in same function (subtotal vs net_sales)

### Pitfall 4: Validation Tolerance Too Strict
**What goes wrong:** Valid invoices fail validation due to rounding differences
**Why it happens:** Kledo might round differently, API arithmetic slightly off
**How to avoid:** Use small tolerance (0.01) in validation, log warnings don't fail
**Warning signs:** Real invoices failing integrity check

### Pitfall 5: Breaking Existing Tests
**What goes wrong:** Tests that mock API responses break after domain model changes
**Why it happens:** Tests used raw Kledo field names, now expect domain model
**How to avoid:** Update test fixtures to use domain model, or test at API boundary
**Warning signs:** Tests pass individually but fail in integration

## Code Examples

Verified patterns from official sources:

### Complete Domain Model Implementation
```python
# File: src/models/invoice_financials.py
# Source: Pydantic docs, project conventions, validated field mapping

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict


class InvoiceFinancials(BaseModel):
    """Financial data for a single invoice with clear business terminology.

    This domain model converts confusing Kledo API field names to standard
    accounting terminology:

    Kledo API -> Domain Model:
    - subtotal -> net_sales (Penjualan Neto, revenue before tax)
    - total_tax -> tax_collected (PPN collected)
    - amount_after_tax -> gross_sales (Penjualan Bruto, total with tax)

    The mathematical relationship is:
        net_sales + tax_collected = gross_sales

    This is validated on instantiation to ensure data integrity.
    """

    model_config = ConfigDict(frozen=True)  # Immutable after creation

    net_sales: Decimal = Field(
        description="Revenue before tax (Penjualan Neto). Source: Kledo 'subtotal'"
    )
    tax_collected: Decimal = Field(
        description="Tax amount collected (PPN). Source: Kledo 'total_tax'"
    )
    gross_sales: Decimal = Field(
        description="Total including tax (Penjualan Bruto). Source: Kledo 'amount_after_tax'"
    )

    # Optional metadata for traceability
    invoice_id: Optional[int] = Field(default=None, description="Source invoice ID")
    ref_number: Optional[str] = Field(default=None, description="Invoice reference number")

    @model_validator(mode='after')
    def validate_financial_integrity(self) -> 'InvoiceFinancials':
        """Validate that net_sales + tax_collected = gross_sales.

        Allows small tolerance (Rp 1) for rounding differences in Kledo API.
        """
        expected = self.net_sales + self.tax_collected
        tolerance = Decimal("1")  # 1 rupiah tolerance
        difference = abs(expected - self.gross_sales)

        if difference > tolerance:
            raise ValueError(
                f"Financial integrity error: "
                f"net_sales ({self.net_sales:,.0f}) + "
                f"tax_collected ({self.tax_collected:,.0f}) = "
                f"{expected:,.0f}, but gross_sales is {self.gross_sales:,.0f}. "
                f"Difference: {difference:,.0f}"
            )
        return self

    @property
    def tax_rate(self) -> Decimal:
        """Calculate effective tax rate as percentage."""
        if self.net_sales == 0:
            return Decimal("0")
        return (self.tax_collected / self.net_sales) * 100
```

### Complete Mapper Implementation
```python
# File: src/mappers/kledo_mapper.py
# Source: Data Mapper pattern, Decimal best practices

from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from src.models.invoice_financials import InvoiceFinancials


def from_kledo_invoice(
    kledo_data: dict[str, Any],
    include_metadata: bool = True
) -> InvoiceFinancials:
    """Convert a single Kledo invoice API response to domain model.

    This function handles the field name mapping:
    - Kledo 'subtotal' -> domain 'net_sales'
    - Kledo 'total_tax' -> domain 'tax_collected'
    - Kledo 'amount_after_tax' -> domain 'gross_sales'

    Args:
        kledo_data: Raw invoice dict from Kledo API response
        include_metadata: If True, include invoice_id and ref_number

    Returns:
        InvoiceFinancials domain model with validated data

    Raises:
        ValueError: If data validation fails (e.g., integrity check)
        KeyError: If required field is missing from kledo_data

    Example:
        >>> inv = from_kledo_invoice({
        ...     "subtotal": 16320000,
        ...     "total_tax": 1795200,
        ...     "amount_after_tax": 18115200,
        ...     "id": 123,
        ...     "ref_number": "INV/26/JAN/01153"
        ... })
        >>> inv.net_sales
        Decimal('16320000')
    """
    # CRITICAL: Convert to str before Decimal to avoid float precision issues
    # Kledo API may return int or float, str() handles both safely

    try:
        net_sales = Decimal(str(kledo_data["subtotal"]))
        tax_collected = Decimal(str(kledo_data["total_tax"]))
        gross_sales = Decimal(str(kledo_data["amount_after_tax"]))
    except (InvalidOperation, TypeError) as e:
        raise ValueError(f"Invalid numeric value in invoice data: {e}")

    kwargs: dict[str, Any] = {
        "net_sales": net_sales,
        "tax_collected": tax_collected,
        "gross_sales": gross_sales,
    }

    if include_metadata:
        kwargs["invoice_id"] = kledo_data.get("id")
        kwargs["ref_number"] = kledo_data.get("ref_number")

    return InvoiceFinancials(**kwargs)


def from_kledo_invoices(
    kledo_invoices: list[dict[str, Any]],
    skip_invalid: bool = False,
    include_metadata: bool = True
) -> list[InvoiceFinancials]:
    """Convert list of Kledo invoices to domain models.

    Args:
        kledo_invoices: List of raw invoice dicts from Kledo API
        skip_invalid: If True, skip invalid invoices with warning;
                      if False, raise on first error
        include_metadata: If True, include invoice_id and ref_number

    Returns:
        List of InvoiceFinancials domain models

    Example:
        >>> invoices = from_kledo_invoices(api_response["data"]["data"])
        >>> total_gross = sum(inv.gross_sales for inv in invoices)
    """
    results: list[InvoiceFinancials] = []

    for i, inv in enumerate(kledo_invoices):
        try:
            results.append(from_kledo_invoice(inv, include_metadata))
        except (ValueError, KeyError) as e:
            if not skip_invalid:
                ref = inv.get("ref_number", f"index {i}")
                raise ValueError(f"Failed to convert invoice {ref}: {e}") from e
            # If skip_invalid, continue to next invoice

    return results


def aggregate_financials(invoices: list[InvoiceFinancials]) -> InvoiceFinancials:
    """Aggregate multiple invoices into a single financial summary.

    Useful for period summaries (monthly revenue, etc.).

    Args:
        invoices: List of InvoiceFinancials to aggregate

    Returns:
        InvoiceFinancials with summed values (no metadata)
    """
    if not invoices:
        return InvoiceFinancials(
            net_sales=Decimal("0"),
            tax_collected=Decimal("0"),
            gross_sales=Decimal("0")
        )

    return InvoiceFinancials(
        net_sales=sum(inv.net_sales for inv in invoices),
        tax_collected=sum(inv.tax_collected for inv in invoices),
        gross_sales=sum(inv.gross_sales for inv in invoices)
    )
```

### Test Examples
```python
# File: tests/test_kledo_mapper.py
# Source: Pytest best practices, project test conventions

import pytest
from decimal import Decimal

from src.models.invoice_financials import InvoiceFinancials
from src.mappers.kledo_mapper import (
    from_kledo_invoice,
    from_kledo_invoices,
    aggregate_financials
)


# Test data based on validated real invoices (see tests/validate_invoice_fields.py)
VALID_INVOICE_DATA = {
    "id": 12345,
    "ref_number": "INV/26/JAN/01153",
    "subtotal": 16320000,
    "total_tax": 1795200,
    "amount_after_tax": 18115200,
}

VALID_ZERO_TAX_DATA = {
    "id": 12346,
    "ref_number": "INV/26/JAN/01154",
    "subtotal": 4410000,
    "total_tax": 0,
    "amount_after_tax": 4410000,
}


class TestFromKledoInvoice:
    """Tests for single invoice conversion."""

    def test_converts_valid_invoice(self):
        """Converts valid Kledo invoice to domain model."""
        result = from_kledo_invoice(VALID_INVOICE_DATA)

        assert result.net_sales == Decimal("16320000")
        assert result.tax_collected == Decimal("1795200")
        assert result.gross_sales == Decimal("18115200")
        assert result.invoice_id == 12345
        assert result.ref_number == "INV/26/JAN/01153"

    def test_converts_zero_tax_invoice(self):
        """Handles invoices with zero tax correctly."""
        result = from_kledo_invoice(VALID_ZERO_TAX_DATA)

        assert result.net_sales == Decimal("4410000")
        assert result.tax_collected == Decimal("0")
        assert result.gross_sales == Decimal("4410000")

    def test_calculates_tax_rate(self):
        """Computed tax_rate property works correctly."""
        result = from_kledo_invoice(VALID_INVOICE_DATA)

        # 1795200 / 16320000 * 100 = 11% (Indonesian PPN)
        assert result.tax_rate == Decimal("11")

    def test_raises_on_missing_field(self):
        """Raises KeyError when required field is missing."""
        invalid_data = {"subtotal": 1000, "total_tax": 100}  # missing amount_after_tax

        with pytest.raises(KeyError):
            from_kledo_invoice(invalid_data)

    def test_raises_on_integrity_failure(self):
        """Raises ValueError when net + tax != gross."""
        bad_data = {
            "subtotal": 1000,
            "total_tax": 100,
            "amount_after_tax": 9999,  # Should be 1100
        }

        with pytest.raises(ValueError, match="Financial integrity error"):
            from_kledo_invoice(bad_data)

    def test_excludes_metadata_when_requested(self):
        """Can exclude metadata from conversion."""
        result = from_kledo_invoice(VALID_INVOICE_DATA, include_metadata=False)

        assert result.invoice_id is None
        assert result.ref_number is None

    def test_handles_float_values_safely(self):
        """Handles float values from API without precision loss."""
        float_data = {
            "subtotal": 16320000.0,  # Float, not int
            "total_tax": 1795200.0,
            "amount_after_tax": 18115200.0,
        }

        result = from_kledo_invoice(float_data, include_metadata=False)
        assert result.net_sales == Decimal("16320000")


class TestFromKledoInvoices:
    """Tests for batch invoice conversion."""

    def test_converts_multiple_invoices(self):
        """Converts list of invoices correctly."""
        invoices = [VALID_INVOICE_DATA, VALID_ZERO_TAX_DATA]

        results = from_kledo_invoices(invoices)

        assert len(results) == 2
        assert results[0].net_sales == Decimal("16320000")
        assert results[1].net_sales == Decimal("4410000")

    def test_skips_invalid_when_requested(self):
        """Skips invalid invoices when skip_invalid=True."""
        bad_data = {"subtotal": 1000, "total_tax": 100, "amount_after_tax": 9999}
        invoices = [VALID_INVOICE_DATA, bad_data, VALID_ZERO_TAX_DATA]

        results = from_kledo_invoices(invoices, skip_invalid=True)

        assert len(results) == 2  # Bad one skipped

    def test_raises_on_invalid_by_default(self):
        """Raises on invalid invoice when skip_invalid=False."""
        bad_data = {"subtotal": 1000, "total_tax": 100, "amount_after_tax": 9999}
        invoices = [VALID_INVOICE_DATA, bad_data]

        with pytest.raises(ValueError, match="Failed to convert invoice"):
            from_kledo_invoices(invoices, skip_invalid=False)


class TestAggregateFinancials:
    """Tests for aggregation function."""

    def test_aggregates_multiple_invoices(self):
        """Sums financial values correctly."""
        inv1 = from_kledo_invoice(VALID_INVOICE_DATA, include_metadata=False)
        inv2 = from_kledo_invoice(VALID_ZERO_TAX_DATA, include_metadata=False)

        result = aggregate_financials([inv1, inv2])

        assert result.net_sales == Decimal("20730000")  # 16320000 + 4410000
        assert result.tax_collected == Decimal("1795200")  # 1795200 + 0
        assert result.gross_sales == Decimal("22525200")  # 18115200 + 4410000

    def test_returns_zeros_for_empty_list(self):
        """Returns zero values for empty invoice list."""
        result = aggregate_financials([])

        assert result.net_sales == Decimal("0")
        assert result.tax_collected == Decimal("0")
        assert result.gross_sales == Decimal("0")
```

### Tool Update Pattern
```python
# Pattern for updating src/tools/revenue.py
# Before: Uses raw Kledo fields
# After: Uses domain model

# BEFORE (current code):
revenue_before_tax = sum(float(safe_get(inv, "subtotal", 0)) for inv in invoices)
total_tax = sum(float(safe_get(inv, "total_tax", 0)) for inv in invoices)
revenue_after_tax = sum(float(safe_get(inv, "amount_after_tax", 0)) for inv in invoices)

# AFTER (with domain model):
from src.mappers.kledo_mapper import from_kledo_invoices, aggregate_financials

# Convert all invoices at once
financial_data = from_kledo_invoices(invoices, skip_invalid=True)
summary = aggregate_financials(financial_data)

# Use clear business terminology
total_net_sales = summary.net_sales
total_tax_collected = summary.tax_collected
total_gross_sales = summary.gross_sales
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw dict with Kledo fields | Pydantic domain model | This phase | Clear code, type safety |
| float for money | Decimal from string | Always recommended | Exact arithmetic |
| Manual validation | Pydantic model_validator | Pydantic v2 | Declarative, automatic |
| Validator decorators | model_validator/field_validator | Pydantic v2 | Cleaner API |

**Deprecated/outdated:**
- `@validator` decorator: Use `@field_validator` in Pydantic v2
- `@root_validator`: Use `@model_validator` in Pydantic v2
- Direct Decimal from float: Always use `Decimal(str(value))`

## Open Questions

Things that couldn't be fully resolved:

1. **Extended InvoiceFinancials Fields**
   - What we know: Core fields (net_sales, tax_collected, gross_sales) are defined
   - What's unclear: Should we add more fields like `discount_amount`, `due`, `paid`?
   - Recommendation: Start minimal with 3 core fields, extend later if needed

2. **Error Handling Strategy**
   - What we know: Validation can fail on bad data
   - What's unclear: Should tools log and continue, or fail fast?
   - Recommendation: Use `skip_invalid=True` in production tools, log warnings

3. **Caching Considerations**
   - What we know: Project already has KledoCache
   - What's unclear: Should domain models be cached, or raw API responses?
   - Recommendation: Cache raw API responses, convert on demand (simpler)

## Sources

### Primary (HIGH confidence)
- [Pydantic Documentation - Validators](https://docs.pydantic.dev/latest/concepts/validators/) - model_validator, field_validator patterns
- [Pydantic Documentation - Fields](https://docs.pydantic.dev/latest/concepts/fields/) - Field, computed_field usage
- [Python decimal module docs](https://docs.python.org/3/library/decimal.html) - Decimal initialization, precision

### Secondary (MEDIUM confidence)
- [Pydantic vs Dataclasses comparison](https://medium.com/@laurentkubaski/pydantic-vs-data-classes-eaa36e01cd77) - When to use each
- [Data Mapper Pattern Wikipedia](https://en.wikipedia.org/wiki/Data_mapper_pattern) - Architecture rationale
- [Decimal pitfalls article](https://pranaysuyash.medium.com/how-i-lost-10-000-because-of-a-python-float-and-how-you-can-avoid-my-mistake-3bd2e5b4094d) - Float vs Decimal financial issues

### Tertiary (Project-specific, HIGH confidence)
- `docs/technical/SESSION_HANDOFF.md` - Complete implementation guide, validated field mappings
- `docs/technical/FIELD_MAPPING_DECISION.md` - Architectural decision rationale
- `tests/validate_invoice_fields.py` - Mathematical proof of field relationships

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Pydantic already in project, well-documented
- Architecture: HIGH - Data Mapper pattern is established, code examples verified
- Pitfalls: HIGH - Float/Decimal issues well-documented, project-specific issues from handoff docs

**Research date:** 2026-01-24
**Valid until:** 2026-02-24 (30 days - stable domain, no fast-moving dependencies)
