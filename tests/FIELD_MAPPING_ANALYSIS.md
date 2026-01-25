# Kledo API Field Mapping Analysis

**Date:** 2026-01-22
**Purpose:** Document actual API response structures vs entity models

## Summary of Findings

The Kledo API follows a **list vs detail pattern**:
- **LIST endpoints** return minimal fields (optimized for performance)
- **DETAIL endpoints** return complete fields (full object data)

This explains why email/phone don't appear in MCP configurator when using list tools!

---

## 1. Contacts

### LIST Endpoint: `/finance/contacts`

**Response Structure:**
```json
{
  "data": {
    "current_page": 1,
    "total": 477,
    "data": [/* array of contacts */]
  }
}
```

**Contact Object (List):**
```json
{
  "id": 1,
  "name": "Samuel Hariandya",
  "company": "PT. KARTIKA EKAYASA",
  "local_id": "0bdb97f2-82cd-4e41-adfb-c4f2635a63a8",
  "receivable_account_id": 21,
  "payable_account_id": 81,
  "payable": "0.00000",
  "receivable": "0.00000",
  "is_archive": 0,
  "type_id": 3,
  "group_id": 1,
  "finance_term_id": null,
  "type_ids": [3],
  "edit_address": null,
  "group": {
    "id": 1,
    "name": "Kontraktor",
    "is_active": true
  },
  "term": null,
  "finance_contact_emails": [],  // ⚠️ Email array - often empty!
  "country": null,
  "province": null,
  "city": null,
  "district": null,
  "village": null
}
```

**Fields Available:**
- ✅ id, name, company
- ✅ payable, receivable (amounts)
- ✅ group (nested object)
- ❌ **NO email field** (only `finance_contact_emails` array which is often empty)
- ❌ **NO phone field**
- ❌ **NO address field** (only location IDs)
- ❌ **NO npwp, fax, description**

---

### DETAIL Endpoint: `/finance/contacts/{id}`

**Response Structure:**
```json
{
  "success": true,
  "data": {/* contact object */}
}
```

**Contact Object (Detail):**
```json
{
  "id": 1,
  "name": "Samuel Hariandya",
  "company": "PT. KARTIKA EKAYASA",
  "address": "KOMPLEK PERKANTORAN CEMPAKA PUTIH BLOK A 19\nJL. LETJEND SUPRAPTO NO. 160",
  "email": "kartikaekayasa@hotmail.com",        // ✅ Email exists!
  "phone": "0214212288",                         // ✅ Phone exists!
  "type_id": 3,
  "receivable_account_id": 21,
  "payable_account_id": 81,
  "group_id": 1,
  "npwp": "016095440025000",
  "is_archive": 0,
  "country_id": 1,
  "province_id": 6,
  "city_id": 58,
  "district_id": null,
  "village_id": null,
  "secondary_phone": null,
  "fax": null,
  "ref_number": null,
  "birthday": null,
  "max_payable": null,
  "max_receivable": null,
  "taxable": 1,
  "photo": null,
  "id_card_type_id": null,
  "id_card_number": null,
  "description": "CIP: Samuel Hariandya - 0823 7070 4269 (Proyek SMPN 30 Depok)",
  "salutation_id": 2,
  "receivable": {/* paginated transactions */},
  "payable": {/* paginated transactions */}
}
```

**Fields Available:**
- ✅ **All fields from list endpoint**
- ✅ **email** (direct field)
- ✅ **phone** (direct field)
- ✅ **address** (full address string)
- ✅ **npwp** (tax ID)
- ✅ **secondary_phone, fax**
- ✅ **description** (notes/memo)
- ✅ **country_id, province_id, city_id** (location IDs instead of nulls)
- ✅ **receivable, payable** (nested transaction lists)

---

## 2. Invoices (Sales)

### LIST Endpoint: `/finance/invoices`

**Response Structure:**
```json
{
  "per_page": 5,
  "current_page": 1,
  "total": 674,
  "data": [/* array of invoices */]
}
```

**Invoice Object (List):**
```json
{
  "id": 13335,
  "business_tran_id": 13289,
  "trans_type_id": 5,
  "trans_date": "2026-01-19",
  "due_date": "2026-01-19",
  "contact_id": 430,
  "status_id": 3,
  "ref_number": "INV/26/JAN/01153",
  "amount": 4410000,
  "amount_after_tax": 4410000,
  "due": 0,
  "include_tax": true,
  "memo": "Villa Mas Nusa Indah - 2 - 169",
  "desc": "",
  "warehouse_id": 1,
  "discount_percent": 0,
  "discount_amount": 0,
  "total_tax": 0,
  "subtotal": 4410000,
  "shipping_cost": 0,
  "payment_date": "2026-01-19",
  "contact": {
    "id": 430,
    "name": "Adil",
    "company": null,
    "npwp": null
  },
  "warehouse": {
    "id": 1,
    "name": "Coating dan Cat"
  },
  "sales_person": {
    "id": 352181,
    "name": "Elmo Abu Abdillah"
  },
  "tags": [
    {
      "id": 1,
      "name": "Penjualan Material",
      "color": "#000000"
    }
  ],
  "attachment_exists": false
}
```

**Fields Available:**
- ✅ Basic invoice data (id, ref_number, dates, amounts)
- ✅ **contact** (nested object with id, name, company)
- ✅ **warehouse** (nested object)
- ✅ **sales_person** (nested object)
- ✅ **tags** (array of tag objects)
- ✅ Financial totals (subtotal, tax, discount, shipping)
- ⚠️ **invoice_items** - NOT VISIBLE (likely need detail endpoint)

---

## 3. Purchase Invoices

**Similar structure to Sales Invoices**
- Uses `/finance/purchaseInvoices` endpoint
- Same pagination pattern
- Similar fields (contact, amounts, dates, status)

---

## 4. Products

**Similar structure to other list endpoints**
- Uses `/finance/products` endpoint
- Returns product list with basic fields
- Likely has separate detail endpoint for full product data

---

## Recommendations

### 1. Update Entity Models

Create **separate models for List vs Detail** responses:

```python
# List response (minimal fields)
class ContactListItem(BaseEntity):
    id: int
    name: str
    company: Optional[str]
    payable: Decimal
    receivable: Decimal
    group: Optional[ContactGroup]
    # NO email, phone, address at this level!

# Detail response (full fields)
class ContactDetail(ContactListItem):
    email: Optional[str]  # ✅ Available here
    phone: Optional[str]  # ✅ Available here
    address: Optional[str]  # ✅ Available here
    npwp: Optional[str]
    secondary_phone: Optional[str]
    fax: Optional[str]
    description: Optional[str]
    # ... all other detail fields
```

### 2. Update Tool Descriptions

Clarify which tools return which fields:

```python
@mcp.tool()
async def contact_list(...):
    \"\"\"
    List contacts (minimal fields).

    **Available fields:**
    - id, name, company
    - payable, receivable amounts
    - group information

    **NOT available in list:**
    - ❌ email (use contact_detail to get email)
    - ❌ phone (use contact_detail to get phone)
    - ❌ full address (use contact_detail)

    **To get email/phone:** Use contact_detail with the contact ID.
    \"\"\"
```

### 3. Add Helper Tools

Create convenience tools for common use cases:

```python
@mcp.tool()
async def contact_search_with_details(...):
    \"\"\"
    Search contacts and fetch full details including email/phone.

    This is a convenience tool that:
    1. Searches contacts using list endpoint
    2. Fetches full details for each match
    3. Returns complete contact information

    Use this when you need email/phone numbers.
    \"\"\"
```

### 4. Document Nested Structures

Some fields are **nested objects**, not flat strings:

```python
# ❌ Wrong assumption
contact.group  # → "Kontraktor"

# ✅ Actual structure
contact.group.name  # → "Kontraktor"
contact.group.id    # → 1
```

---

## Next Steps

1. ✅ Test all 4 priority endpoints
2. ⏳ Create field mapping for each endpoint type
3. ⏳ Update entity models (List vs Detail variants)
4. ⏳ Update tool descriptions with field availability
5. ⏳ Create helper tools for common patterns
6. ⏳ Add validation tests to catch future mismatches

---

**Generated:** 2026-01-22
**Tool:** tests/test_api_structure.py
