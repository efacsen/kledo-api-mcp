# Field Mapping Decision Analysis

**Question:** Should we convert Kledo API fields to our own naming system?

**Date:** January 24, 2026
**Decision Status:** 🤔 Analysis for Discussion

---

## 🎯 The Problem

Kledo API uses field names that can be confusing:

```python
# Kledo API fields (actual data):
{
    "subtotal": 16320000,          # What subtotal? Of what?
    "total_tax": 1795200,           # OK, clear
    "amount_after_tax": 18115200    # Confusing! "after" suggests subtraction,
                                    # but actually means "including tax"
}
```

**Confusion Points:**
1. ❌ `amount_after_tax` sounds like tax was subtracted, but actually tax was ADDED
2. ❌ `subtotal` is vague - subtotal of what?
3. ❌ International developers will misinterpret these terms

---

## 🔄 Option 1: Keep Kledo Fields As-Is (No Conversion)

### Approach
Use Kledo field names directly throughout our system:

```python
# Example usage:
revenue_report = {
    "subtotal": 16320000,
    "total_tax": 1795200,
    "amount_after_tax": 18115200
}

# In analytics:
total_revenue_before_tax = sum(inv["subtotal"] for inv in invoices)
total_revenue_with_tax = sum(inv["amount_after_tax"] for inv in invoices)
```

### ✅ Pros
1. **Simple & Direct**
   - No mapping layer needed
   - One less thing to maintain
   - Direct passthrough from API to reports

2. **Performance**
   - Zero conversion overhead
   - No CPU cycles wasted on renaming
   - Smaller memory footprint

3. **API Alignment**
   - Easy to debug (field names match API docs)
   - Easy to trace data flow
   - Clear when looking at API responses

4. **Less Code**
   - No mapping functions to write
   - No conversion bugs possible
   - Fewer lines of code

### ❌ Cons
1. **Confusing Naming**
   - `amount_after_tax` misleading for international teams
   - `subtotal` too vague
   - Need heavy documentation

2. **Tight Coupling**
   - System depends on Kledo's naming choices
   - If Kledo changes field names → we break
   - Hard to switch to different accounting system

3. **Domain Knowledge Required**
   - Every developer needs to understand Kledo's naming
   - Onboarding new devs takes longer
   - Risk of misuse (thinking "after_tax" means minus tax)

4. **Business Communication Gap**
   - Finance team talks about "Penjualan Bruto/Neto"
   - Code talks about "subtotal/amount_after_tax"
   - Translation layer in conversations

### 💰 Cost Analysis
- **Development Time:** 0 hours (nothing to build)
- **Maintenance:** Low (no mapping to update)
- **Onboarding:** Medium (need to explain Kledo naming)
- **Risk of Bugs:** Low (no conversion = no conversion bugs)

---

## 🔄 Option 2: Convert to Clear Domain Names

### Approach
Create a domain model with clear, unambiguous names:

```python
# Domain model (our names):
class InvoiceRevenue:
    gross_sales: Decimal          # Total paid by customer (with tax)
    tax_collected: Decimal        # PPN collected
    net_sales: Decimal            # Revenue before tax

# Conversion layer:
def from_kledo_invoice(kledo_data: dict) -> InvoiceRevenue:
    """Convert Kledo API fields to our domain model."""
    return InvoiceRevenue(
        gross_sales=Decimal(kledo_data["amount_after_tax"]),
        tax_collected=Decimal(kledo_data["total_tax"]),
        net_sales=Decimal(kledo_data["subtotal"])
    )

# Usage in analytics:
revenue_report = {
    "gross_sales": 18115200,      # Clear: total including tax
    "tax_collected": 1795200,      # Clear: tax amount
    "net_sales": 16320000          # Clear: revenue before tax
}
```

### ✅ Pros
1. **Crystal Clear Naming**
   - `gross_sales` = obvious (total transaction)
   - `net_sales` = obvious (company's revenue)
   - `tax_collected` = obvious (PPN)
   - Zero ambiguity, international standard terms

2. **Business Alignment**
   - Matches finance team terminology
   - Matches accounting standards
   - Easier communication across teams

3. **Loose Coupling**
   - System independent of Kledo's naming
   - Easy to switch accounting systems
   - Changes in Kledo API only affect mapping layer

4. **Self-Documenting Code**
   ```python
   # This is clear:
   if invoice.net_sales > 10_000_000:
       apply_volume_discount()

   # vs this (confusing):
   if invoice.subtotal > 10_000_000:
       apply_volume_discount()  # subtotal of what?
   ```

5. **Type Safety**
   - Can add validation in conversion
   - Enforce business rules (net + tax = gross)
   - Catch data inconsistencies early

### ❌ Cons
1. **Extra Layer to Maintain**
   - Conversion functions need maintenance
   - If Kledo adds fields → update mapping
   - More code = more potential bugs

2. **Performance Overhead** (minimal)
   - Extra function calls
   - Memory for duplicated data structures
   - (But negligible in practice)

3. **Development Time**
   - Need to write conversion layer (~4-8 hours)
   - Need to write tests for conversion
   - Need to update existing code

4. **Two Sources of Truth** (if not careful)
   - Risk of using wrong model in wrong place
   - Need clear boundaries: "API layer uses Kledo, domain layer uses our model"

### 💰 Cost Analysis
- **Development Time:** 4-8 hours initial setup
- **Maintenance:** Medium (update mapping when API changes)
- **Onboarding:** Low (clear names = easy to understand)
- **Risk of Bugs:** Medium (conversion bugs possible, but testable)

---

## 🏗️ Recommended Architecture (Hybrid Approach)

### Best Practice: Separation of Concerns

```python
# Layer 1: API/Data Layer (Kledo fields)
class KledoInvoiceData:
    """Raw data from Kledo API - field names match API exactly."""
    subtotal: int
    total_tax: int
    amount_after_tax: int

# Layer 2: Domain/Business Layer (Our names)
class InvoiceFinancials:
    """Business domain model - clear, unambiguous names."""
    net_sales: Decimal          # Revenue before tax
    tax_collected: Decimal      # PPN collected
    gross_sales: Decimal        # Total transaction value

    @classmethod
    def from_kledo(cls, data: KledoInvoiceData) -> "InvoiceFinancials":
        """Convert Kledo data to domain model."""
        return cls(
            net_sales=Decimal(data.subtotal),
            tax_collected=Decimal(data.total_tax),
            gross_sales=Decimal(data.amount_after_tax)
        )

    def validate(self):
        """Ensure data integrity."""
        assert self.net_sales + self.tax_collected == self.gross_sales

# Layer 3: Presentation Layer (Reports)
def generate_revenue_report(invoices: List[InvoiceFinancials]) -> dict:
    """Generate report using domain model."""
    return {
        "penjualan_bruto": sum(inv.gross_sales for inv in invoices),
        "ppn_collected": sum(inv.tax_collected for inv in invoices),
        "penjualan_neto": sum(inv.net_sales for inv in invoices)
    }
```

### Layer Boundaries

```
┌─────────────────────────────────────────────────────┐
│ PRESENTATION LAYER                                  │
│ - Dashboards, Reports, API responses                │
│ - Uses: Domain model (InvoiceFinancials)            │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ BUSINESS/DOMAIN LAYER                               │
│ - Analytics, Calculations, Business Logic           │
│ - Uses: Domain model (InvoiceFinancials)            │
│ - Names: gross_sales, net_sales, tax_collected      │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ CONVERSION LAYER (Adapter Pattern)                  │
│ - from_kledo() mapping functions                    │
│ - Validation & data integrity checks                │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ DATA/API LAYER                                      │
│ - Kledo API client                                  │
│ - Uses: Kledo field names (as-is)                   │
│ - Names: subtotal, amount_after_tax, total_tax      │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Decision Matrix

| Criteria | No Conversion | With Conversion | Weight |
|----------|---------------|-----------------|--------|
| **Code Clarity** | 3/10 (confusing) | 9/10 (crystal clear) | HIGH |
| **Maintenance** | 8/10 (simple) | 6/10 (extra layer) | MEDIUM |
| **Performance** | 10/10 (zero overhead) | 9/10 (negligible) | LOW |
| **Onboarding** | 5/10 (need docs) | 9/10 (self-evident) | HIGH |
| **Future-Proof** | 4/10 (tight coupling) | 9/10 (loose coupling) | HIGH |
| **Dev Time** | 10/10 (zero) | 7/10 (4-8 hours) | MEDIUM |
| **Bug Risk** | 9/10 (no conversion bugs) | 7/10 (testable) | MEDIUM |

**Weighted Score:**
- No Conversion: **5.8/10**
- With Conversion: **8.2/10** ✅

---

## 💡 My Recommendation: **Convert (Option 2)**

### Why Convert?

1. **Long-term Investment**
   - Yes, takes 4-8 hours now
   - But saves 100+ hours over project lifetime
   - Every developer instantly understands code

2. **Professional Quality**
   - Clear domain models = production-grade system
   - Messy field names = prototype-grade
   - We're building analytics platform, not throwaway script

3. **Team Scalability**
   - New developers productive immediately
   - Finance team can read code directly
   - No "Kledo naming translation" needed

4. **Risk Mitigation**
   - If Kledo changes API → only mapper breaks
   - If we switch accounting systems → only mapper changes
   - Business logic stays clean

### When NOT to Convert?

Only keep Kledo names if:
- ❌ This is temporary/POC code (< 3 months lifespan)
- ❌ Only 1 developer will ever touch this
- ❌ No plans to grow beyond basic reports
- ❌ Time pressure is extreme (< 1 week to ship)

Otherwise: **Convert to domain model**

---

## 🔨 Implementation Plan (If Converting)

### Phase 1: Define Domain Model (1 hour)
```python
# src/models/domain.py
from decimal import Decimal
from dataclasses import dataclass

@dataclass
class InvoiceFinancials:
    """Financial data for a single invoice."""
    net_sales: Decimal          # Penjualan Neto (before tax)
    tax_collected: Decimal      # PPN collected
    gross_sales: Decimal        # Penjualan Bruto (with tax)

    def __post_init__(self):
        """Validate data integrity."""
        expected_gross = self.net_sales + self.tax_collected
        if abs(expected_gross - self.gross_sales) > Decimal("0.01"):
            raise ValueError(
                f"Data integrity error: net_sales ({self.net_sales}) + "
                f"tax_collected ({self.tax_collected}) != "
                f"gross_sales ({self.gross_sales})"
            )
```

### Phase 2: Create Mapper (2 hours)
```python
# src/mappers/kledo_mapper.py

def map_invoice_financials(kledo_invoice: dict) -> InvoiceFinancials:
    """
    Convert Kledo invoice to domain model.

    Kledo API uses confusing names:
    - "amount_after_tax" = gross sales (WITH tax)
    - "subtotal" = net sales (BEFORE tax)
    - "total_tax" = tax collected

    We normalize to clear terms:
    - gross_sales = total transaction (what customer pays)
    - net_sales = revenue before tax (what company keeps)
    - tax_collected = PPN that goes to government
    """
    return InvoiceFinancials(
        net_sales=Decimal(str(kledo_invoice["subtotal"])),
        tax_collected=Decimal(str(kledo_invoice["total_tax"])),
        gross_sales=Decimal(str(kledo_invoice["amount_after_tax"]))
    )
```

### Phase 3: Update Tools (3 hours)
```python
# src/tools/revenue.py (updated)

async def _revenue_summary(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get revenue summary using domain model."""

    # Fetch from API (Kledo fields)
    kledo_data = await client.list_invoices(...)
    invoices = kledo_data.get("data", {}).get("data", [])

    # Convert to domain model
    financial_data = [
        map_invoice_financials(inv)
        for inv in invoices
    ]

    # Calculate using clear names
    total_gross_sales = sum(inv.gross_sales for inv in financial_data)
    total_net_sales = sum(inv.net_sales for inv in financial_data)
    total_tax = sum(inv.tax_collected for inv in financial_data)

    # Report with business terminology
    return f"""
# Revenue Summary

**Period**: {date_from} to {date_to}
**Paid Invoices**: {len(financial_data)}

## Financial Overview
**Penjualan Bruto (Gross Sales)**: Rp {total_gross_sales:,.0f}
**PPN Collected**: Rp {total_tax:,.0f}
**Penjualan Neto (Net Sales)**: Rp {total_net_sales:,.0f}
"""
```

### Phase 4: Write Tests (2 hours)
```python
# tests/test_kledo_mapper.py

def test_kledo_to_domain_conversion():
    """Test mapping from Kledo fields to domain model."""
    kledo_data = {
        "subtotal": 16320000,
        "total_tax": 1795200,
        "amount_after_tax": 18115200
    }

    result = map_invoice_financials(kledo_data)

    assert result.net_sales == Decimal("16320000")
    assert result.tax_collected == Decimal("1795200")
    assert result.gross_sales == Decimal("18115200")

def test_data_integrity_validation():
    """Test that conversion validates data integrity."""
    bad_data = {
        "subtotal": 16320000,
        "total_tax": 1795200,
        "amount_after_tax": 99999999  # Wrong!
    }

    with pytest.raises(ValueError, match="Data integrity error"):
        map_invoice_financials(bad_data)
```

---

## 📈 Long-term Benefits

### Scenario 1: New Developer Joins
**Without Conversion:**
```python
# They see this and think:
revenue_before_tax = invoice["amount_after_tax"]  # Wait, what??
# Needs 30 minutes explanation + docs
```

**With Conversion:**
```python
# They see this and understand immediately:
revenue_before_tax = invoice.net_sales  # Clear!
# Zero explanation needed
```

**Time Saved:** 30 min × every new developer = Hours saved

---

### Scenario 2: Switch to Different Accounting System
**Without Conversion:**
```python
# Need to find and update 50+ places where "subtotal" is used
# Risk: miss some, introduce bugs
```

**With Conversion:**
```python
# Only update mapper.py (1 file, 10 lines)
# All business logic stays the same
```

**Time Saved:** Days of refactoring avoided

---

### Scenario 3: Finance Team Reviews Code
**Without Conversion:**
```
Finance: "Where's Penjualan Bruto?"
Dev: "That's amount_after_tax"
Finance: "But 'after tax' means minus tax?"
Dev: "No, in Kledo it means plus tax"
Finance: "That's confusing..."
```

**With Conversion:**
```
Finance: "I see gross_sales, net_sales - perfect!"
Dev: "Yep, matches your terminology exactly"
Finance: "Easy to audit!"
```

**Benefit:** Zero communication gap

---

## 🎯 Final Recommendation

### For Your Kledo MCP Project:

**DO CONVERT** because:

1. ✅ You're building analytics platform (long-term)
2. ✅ Finance team will use this (business alignment critical)
3. ✅ May add more features later (scalability matters)
4. ✅ Only 4-8 hours investment (minimal cost)
5. ✅ Reduces future confusion/bugs (ROI positive)

### Implementation Strategy:

```
Week 1:
- Define domain model (InvoiceFinancials)
- Create mapper (kledo_mapper.py)
- Write tests

Week 2:
- Update 3 most-used tools (revenue, invoice, sales_analytics)
- Validate with real queries

Week 3:
- Update remaining tools
- Update documentation
- Team review
```

**Total Time:** ~12 hours spread over 3 weeks
**Long-term Savings:** 100+ hours over 1 year

---

## 📚 References

- **Domain-Driven Design** (Eric Evans): Separate domain model from data model
- **Clean Architecture** (Robert Martin): Dependencies point inward, domain is independent
- **Adapter Pattern**: Convert external API to internal model

---

**Decision:** Convert Kledo fields to clear domain names ✅
**Rationale:** Long-term code quality > short-term convenience
**Next Step:** Implement domain model + mapper (4-8 hours)
