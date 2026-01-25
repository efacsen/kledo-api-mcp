# Critical Missing Fields Summary

**Generated:** 2026-01-22
**Purpose:** Quick reference for fields missing in LIST endpoints

Full details: `tests/list_vs_detail_comparison.txt`

---

## Overview

All Kledo API endpoints follow the **LIST vs DETAIL pattern**:
- **LIST endpoints** return minimal fields (27-91 fields)
- **DETAIL endpoints** return complete data (150-362 fields)

**Impact:** MCP tools using LIST endpoints are missing 60-80% of available data!

---

## 1. CONTACTS 📇

**LIST fields:** 27
**DETAIL fields:** 177
**Missing:** 150 fields (85% of data!)

### 🔴 Critical Missing Fields

| Field | Example Value | Why It Matters |
|-------|---------------|----------------|
| **email** | `kartikaekayasa@hotmail.com` | Primary contact method |
| **phone** | `0214212288` | Primary contact method |
| **address** | `KOMPLEK PERKANTORAN...` | Full address string |
| **npwp** | `016095440025000` | Tax ID for invoices |
| **description** | `CIP: Samuel Hariandya...` | Notes/memo field |
| **secondary_phone** | `null` | Alternative contact |
| **fax** | `null` | Fax number |
| **city** | `{id: 58, name: "Jakarta Pusat"}` | Location details |
| **province** | `{id: 6, name: "DKI Jakarta"}` | Location details |
| **country** | `{id: 1, name: "Indonesia"}` | Location details |
| **transactions** | Array of past transactions | Transaction history |
| **count.payment_received** | `8` | Transaction count |
| **total.payment_received** | `177324997.5` | Total revenue |

### What LIST Provides

- ✅ id, name, company
- ✅ payable/receivable amounts
- ✅ group (nested object)
- ❌ NO contact information (email, phone, address)
- ❌ NO transaction history
- ❌ NO location details (only IDs, not names)

---

## 2. SALES INVOICES 🧾

**LIST fields:** 91
**DETAIL fields:** 362
**Missing:** 292 fields (81% of data!)

### 🔴 Critical Missing Fields

| Field | Why It Matters |
|-------|----------------|
| **items** | Invoice line items (products, quantities, prices) |
| **items[].product** | Full product details for each line item |
| **contact.email** | Customer email for invoice |
| **contact.phone** | Customer phone for invoice |
| **contact.address** | Customer address for invoice |
| **log.action** | Who created/modified the invoice |
| **log.print** | Print history |
| **order** | Related sales order (if converted) |
| **parent_tran** | Parent transaction reference |
| **payment_connect** | Payment gateway info |
| **print_url** | URL to print invoice PDF |
| **print_url_receipt** | URL to print payment receipt |
| **is_deletable** | Can this invoice be deleted? |
| **is_editable** | Can this invoice be edited? |
| **is_voidable** | Can this invoice be voided? |

### What LIST Provides

- ✅ Basic invoice data (id, ref_number, dates)
- ✅ Amounts (subtotal, tax, shipping, total)
- ✅ Contact summary (id, name, company)
- ✅ Status, warehouse, sales person
- ✅ Tags
- ❌ NO invoice line items
- ❌ NO customer contact info (email, phone, address)
- ❌ NO full product details
- ❌ NO audit log
- ❌ NO print URLs

---

## 3. PURCHASE INVOICES 💸

**Similar to Sales Invoices**
- **Missing:** ~280-300 fields
- Same pattern: LIST has summary, DETAIL has items + full data

### 🔴 Critical Missing Fields

- **items** (line items with products)
- **supplier contact info** (email, phone, address)
- **payment details**
- **audit log**

---

## 4. PRODUCTS 📦

**LIST fields:** ~40-60 (estimate)
**DETAIL fields:** ~150-200 (estimate)

### 🔴 Expected Missing Fields

- Full product description
- Multiple prices (wholesale, retail, bulk)
- Stock levels by warehouse
- Product variants/options
- Supplier information
- Purchase/sell accounts
- Serial number tracking config

---

## 5. ORDERS 📋

**Similar pattern to Invoices**

### 🔴 Expected Missing Fields

- Order line items
- Customer contact details
- Shipping information
- Related invoices/deliveries

---

## Impact on MCP Tools

### Current State (Using LIST endpoints)

```python
@mcp.tool()
async def contact_list():
    # Returns 27 fields per contact
    # ❌ NO email
    # ❌ NO phone
    # ❌ NO address
```

**Result:** MCP configurator UI shows contact names but can't display email/phone!

### What We Need (DETAIL endpoints)

```python
@mcp.tool()
async def contact_detail(contact_id: int):
    # Returns 177 fields per contact
    # ✅ email: "kartikaekayasa@hotmail.com"
    # ✅ phone: "0214212288"
    # ✅ address: "KOMPLEK PERKANTORAN..."
```

---

## Recommendations

### Option A: Hybrid Approach (Recommended)

1. **Keep LIST tools** for browsing/searching
   - Fast, lightweight
   - Good for finding IDs
   - Good for summaries

2. **Add DETAIL tools** for complete data
   - `contact_detail(id)` → full contact with email/phone
   - `invoice_detail(id)` → invoice with line items
   - `product_detail(id)` → full product specs

3. **Add convenience tools** that combine both
   - `contact_search_with_details(query)` → search + fetch full details
   - `invoice_get_with_items(id)` → invoice + line items in one call

### Option B: Always Use DETAIL (Not Recommended)

- ❌ Slower (more data transferred)
- ❌ More API load
- ❌ Higher latency
- ✅ Always have complete data

### Option C: Augmented LIST

Add most critical fields to LIST responses by calling DETAIL selectively:
- Only fetch DETAIL for top 5-10 results
- User can request "show more" to fetch remaining

---

## Next Steps

1. **Review this summary** - Which fields matter most to you?
2. **Prioritize entities** - Which ones do you use most? (Contacts, Invoices, Products?)
3. **Choose approach** - Hybrid (separate LIST/DETAIL tools) or convenience tools?
4. **Update entity models** - Create separate Pydantic models for LIST vs DETAIL
5. **Add new tools** - Implement DETAIL endpoint tools
6. **Update documentation** - Clarify which tool provides which fields

---

**Full comparison data:** See `tests/list_vs_detail_comparison.txt` for complete field lists for all 8 entity types tested.
