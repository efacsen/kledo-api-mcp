# Kledo API MCP Server - Architecture Documentation

**Last Updated:** January 24, 2026
**Version:** 1.0.0
**Status:** Production-Ready with Consolidation Opportunity

---

## Executive Summary

### Current State
- **Total Tools:** 25 MCP tools
- **Active Usage:** 5 tools (20%) serve 100% of real business queries
- **Token Cost:** ~5,000-7,500 tokens per request
- **API Health:** ✅ Working perfectly, full data available

### Key Finding
**80% of tools are unused** in realistic business workflows, consuming tokens without providing value.

### Tested Business Queries (All Successful)
1. ✅ Revenue analysis (monthly, weekly, daily)
2. ✅ Sales rep performance tracking
3. ✅ Invoice lifecycle monitoring (created, paid, outstanding)
4. ✅ Top customer identification
5. ✅ Commission calculation data retrieval

---

## API Endpoints Configuration

### Base URL Structure
```
https://yourcompany.api.kledo.com/api/v1
```

### Authentication
```python
# Recommended: API Key
KLEDO_API_KEY=kledo_pat_xxx...

# Legacy: Email/Password
KLEDO_EMAIL=user@example.com
KLEDO_PASSWORD=xxx
```

### Available Endpoint Categories (13 total)

| Category | Endpoints | Status | Usage in Real Workflows |
|----------|-----------|--------|------------------------|
| **invoices** | list, detail, totals | ✅ Active | 🔥 High (3× in tests) |
| **reports** | activity_team, profit_loss, etc. | ✅ Ready | ❌ Unused |
| **purchase_invoices** | list, detail, totals | ✅ Ready | ❌ Unused |
| **orders** | list, detail, totals | ✅ Ready | ❌ Unused |
| **purchase_orders** | list, detail, totals | ✅ Ready | ❌ Unused |
| **products** | list, detail, suggestion | ✅ Ready | ❌ Unused |
| **contacts** | list, detail, transactions | ✅ Ready | ⚠️ Low (1× in tests) |
| **deliveries** | list, detail, totals | ✅ Ready | ❌ Unused |
| **purchase_deliveries** | list, detail | ✅ Ready | ❌ Unused |
| **bank** | transactions, balances | ✅ Ready | ❌ Unused |
| **accounts** | list, detail | ✅ Ready | ❌ Unused |
| **supporting** | units, tags, fees, warehouses | ✅ Ready | ❌ Unused |

---

## Data Structures

### Invoice Entity (Primary)

**API Endpoint:** `/finance/invoices`

#### Complete Field List (75+ fields available)
```python
{
  # Core Identification
  'id': 13454,
  'business_tran_id': 13448,
  'ref_number': 'INV/26/JAN/01161',
  'trans_type_id': 5,

  # Dates
  'trans_date': '2026-01-23',
  'due_date': '2026-01-23',
  'payment_date': '2026-01-23',
  'paid_date': '2026-01-23',
  'shipping_date': None,
  'created_at': '2026-01-23',
  'updated_at': '2026-01-23',

  # Financial Amounts (IDR)
  'subtotal': 16320000,              # Before tax
  'total_tax': 1795200,               # Tax amount
  'amount_after_tax': 18115200,       # After tax (subtotal + tax)
  'amount': 16320000,                 # Base amount
  'due': 0,                           # Outstanding amount
  'discount_amount': 0,
  'discount_percent': 0,
  'additional_discount_amount': 0,
  'additional_discount_percent': 0,
  'shipping_cost': 0,
  'witholding_amount': 0,
  'witholding_percent': 0,

  # Status & Payment
  'status_id': 3,                     # 1=Unpaid, 2=Partial, 3=Paid
  'due_days': 0,                      # Days overdue
  'pay_later': False,
  'include_tax': False,

  # Relationships (IDs)
  'contact_id': 489,
  'sales_id': 230701,                 # Sales rep ID (KEY for commissions!)
  'owner_id': 218933,
  'warehouse_id': 1,
  'term_id': 5,                       # Payment terms

  # Nested Objects (FULL DATA AVAILABLE)
  'contact': {
    'id': 489,
    'name': 'Tahroni Arifin',
    'company': 'PT. RANGKA RUANG INDONESIA',
    'npwp': '509721197002000'         # Tax ID
  },

  'sales_person': {
    'id': 230701,
    'name': 'Ahmad Kurniawan'  # Sales rep name (KEY!)
  },

  'warehouse': {
    'id': 1,
    'name': 'Coating dan Cat'
  },

  'termin': {
    'id': 5,
    'name': 'Cash Before Delivery'    # Payment terms
  },

  'tags': [{
    'id': 1,
    'name': 'Penjualan Material',
    'color': '#000000'
  }],

  # Additional Details
  'memo': 'Stadion Wibawa Mukti Bekasi - 452',
  'desc': '',
  'order_number': 'SO/26/JAN/00838',
  'qty': 24,
  'print_status': 'Belum',
  'attachment': [],
  'attachment_exists': False,

  # Currency (not typically used for IDR)
  'currency_id': 0,
  'currency_rate': 1,

  # Payment Accounts
  'payment_accounts': [{
    'id': 1507,
    'name': 'Mandiri Main 6667',
    'name_id': 'Mandiri Main 6667'
  }]
}
```

#### Key Fields for Business Queries

##### Revenue Calculation
```python
# Revenue Before Tax
revenue_before_tax = sum(invoice['subtotal'] for invoice in invoices)

# Tax Amount
total_tax = sum(invoice['total_tax'] for invoice in invoices)

# Revenue After Tax
revenue_after_tax = sum(invoice['amount_after_tax'] for invoice in invoices)
```

##### Status Filtering
```python
status_mapping = {
    1: "Belum Dibayar / Unpaid",
    2: "Dibayar Sebagian / Partially Paid",
    3: "Lunas / Paid"
}

# Get only paid invoices for revenue
paid_invoices = [inv for inv in invoices if inv['status_id'] == 3]

# Get outstanding (unpaid + partial)
outstanding = [inv for inv in invoices if inv['status_id'] in [1, 2]]
```

##### Sales Rep Performance
```python
# Group revenue by sales rep
from collections import defaultdict

rep_revenue = defaultdict(lambda: {
    'total_before_tax': 0,
    'total_after_tax': 0,
    'invoice_count': 0,
    'rep_name': ''
})

for invoice in paid_invoices:
    sales_id = invoice['sales_id']
    rep_revenue[sales_id]['total_before_tax'] += invoice['subtotal']
    rep_revenue[sales_id]['total_after_tax'] += invoice['amount_after_tax']
    rep_revenue[sales_id]['invoice_count'] += 1
    rep_revenue[sales_id]['rep_name'] = invoice['sales_person']['name']
```

##### Customer Analysis
```python
# Top customers by revenue
customer_revenue = defaultdict(lambda: {
    'total_revenue': 0,
    'invoice_count': 0,
    'customer_name': '',
    'company': ''
})

for invoice in paid_invoices:
    contact_id = invoice['contact_id']
    customer_revenue[contact_id]['total_revenue'] += invoice['amount_after_tax']
    customer_revenue[contact_id]['invoice_count'] += 1
    customer_revenue[contact_id]['customer_name'] = invoice['contact']['name']
    customer_revenue[contact_id]['company'] = invoice['contact'].get('company', '')

# Sort by revenue
top_customers = sorted(
    customer_revenue.items(),
    key=lambda x: x[1]['total_revenue'],
    reverse=True
)[:10]
```

---

## Current Tool Architecture (25 Tools)

### 1. Financial Reports (4 tools) - ❌ UNUSED
```python
financial_activity_team_report(date_from, date_to)
financial_sales_summary(date_from, date_to)
financial_purchase_summary(date_from, date_to)
financial_bank_balances()
```

**Status:** Implemented but not called in real workflows.

---

### 2. Products (3 tools) - ❌ UNUSED
```python
product_list(page=1, per_page=50, search=None)
product_get_detail(product_id)
product_search_by_sku(sku)
```

**Status:** Ready but not needed for current queries.

---

### 3. Utilities (3 tools) - ❌ UNUSED
```python
utility_clear_cache()
utility_get_cache_stats()
utility_test_connection()
```

**Status:** System tools, rarely needed in business workflows.

---

### 4. Contacts (3 tools) - ⚠️ LOW USAGE
```python
contact_list(page=1, per_page=50, search=None)
contact_get_detail(contact_id)
contact_get_transactions(contact_id)  # ✅ Used 1× in tests
```

**Usage:** Only transactions endpoint used (customer analysis).
**Note:** Contact info already embedded in invoice responses!

---

### 5. Deliveries (3 tools) - ❌ UNUSED
```python
delivery_list(date_from=None, date_to=None, status_id=None)
delivery_get_detail(delivery_id)
delivery_get_pending()
```

**Status:** Not needed for current financial workflows.

---

### 6. Orders (3 tools) - ❌ UNUSED
```python
order_list_sales(date_from=None, date_to=None)
order_get_detail(order_id)
order_list_purchase(date_from=None, date_to=None)
```

**Status:** Not queried in revenue/commission workflows.

---

### 7. Sales Analytics (2 tools) - 🔥 HIGH USAGE
```python
sales_rep_revenue_report(date_from, date_to)  # ✅ Used 2× in tests
sales_rep_list()                               # ✅ Used 1× in tests
```

**Status:** CRITICAL for commission calculations.
**Fields Used:**
- `sales_rep_name`
- `total_revenue` (before and after tax)
- `invoice_count`

---

### 8. Revenue & Receivables (3 tools) - 🔥 HIGH USAGE
```python
revenue_summary(date_from, date_to)                    # ✅ Used 3× in tests
outstanding_receivables(status_id=None, min_amount=0)
customer_revenue_ranking(date_from, date_to, top_n=10) # ✅ Used 1× in tests
```

**Status:** CORE tools for financial analysis.
**Test Results (Jan 2026 data):**
```
Revenue Before Tax: Rp 92,823,250.00
Tax (PPN): Rp 8,678,450.00
Revenue After Tax: Rp 101,501,700.00
Paid Invoices: 16
```

---

### 9. Invoices (4 tools) - 🔥 HIGH USAGE
```python
invoice_list_sales(date_from, date_to, status=None)  # ✅ Used 3× in tests
invoice_get_detail(invoice_id)
invoice_get_totals(date_from, date_to, status=None)
invoice_list_purchase(date_from, date_to, status=None)
```

**Status:** ESSENTIAL for all revenue and invoice queries.
**Most Used Tool:** `invoice_list_sales` (3 calls for different status filters).

---

## Tool Usage Analysis (From Testing)

### Test Date: January 24, 2026
### Test Queries: 9 realistic business scenarios

| Tool Name | Call Count | Purpose | Status |
|-----------|-----------|---------|--------|
| `revenue_summary` | 3× | Monthly/weekly/daily revenue | ✅ CRITICAL |
| `invoice_list_sales` | 3× | Created/paid/outstanding invoices | ✅ CRITICAL |
| `sales_rep_revenue_report` | 2× | Commission calculations | ✅ CRITICAL |
| `customer_revenue_ranking` | 1× | Top customer identification | ✅ IMPORTANT |
| `sales_rep_list` | 1× | Sales rep enumeration | ✅ IMPORTANT |
| **All other tools (20)** | 0× | - | ❌ UNUSED |

### Coverage Statistics
- **Tools Used:** 5 / 25 (20%)
- **Tools Unused:** 20 / 25 (80%)
- **Token Overhead:** ~4,000-6,000 tokens/request wasted on unused tool definitions

---

## Consolidation Recommendation

### Proposed Architecture: 25 → 6 Tools

#### **Tool 1: `kledo_revenue`** (replaces 3 tools)
```python
kledo_revenue(
    operation: "summary" | "receivables" | "customer_ranking",
    date_from: str = None,
    date_to: str = None,
    filters: dict = {}
)
```

**Handles:**
- Revenue summaries (monthly, weekly, custom ranges)
- Outstanding receivables tracking
- Top customer rankings

**Token Savings:** ~600-900 tokens/request

---

#### **Tool 2: `kledo_invoice`** (replaces 4 tools)
```python
kledo_invoice(
    operation: "list_sales" | "list_purchase" | "get_detail" | "get_totals",
    invoice_id: int = None,
    date_from: str = None,
    date_to: str = None,
    status: str = None,  # "paid", "unpaid", "partial"
    filters: dict = {}
)
```

**Handles:**
- Invoice listing (sales/purchase)
- Invoice details
- Invoice totals and summaries
- Status-based filtering

**Token Savings:** ~800-1,200 tokens/request

---

#### **Tool 3: `kledo_sales_analytics`** (replaces 2 tools)
```python
kledo_sales_analytics(
    operation: "revenue_report" | "rep_list" | "commission_calc",
    date_from: str = None,
    date_to: str = None,
    sales_rep_id: int = None,
    filters: dict = {}
)
```

**Handles:**
- Sales rep performance reports
- Sales rep enumeration
- Commission calculation support

**Token Savings:** ~400-600 tokens/request

---

#### **Tool 4: `kledo_contact`** (consolidates 3 tools, keep for completeness)
```python
kledo_contact(
    operation: "list" | "get_detail" | "get_transactions",
    contact_id: int = None,
    filters: dict = {}
)
```

**Handles:**
- Customer/vendor listing
- Contact details
- Transaction history

**Usage:** Low but may be needed for future queries.

---

#### **Tool 5: `kledo_product`** (consolidates 3 tools, defer)
```python
kledo_product(
    operation: "list" | "get_detail" | "search_sku",
    product_id: int = None,
    sku: str = None,
    filters: dict = {}
)
```

**Status:** Not used in current workflows, but keep for completeness.

---

#### **Tool 6: `kledo_utility`** (keep as-is, 3 tools)
```python
kledo_utility(
    operation: "clear_cache" | "cache_stats" | "test_connection"
)
```

**Status:** System utilities, rarely called but useful for debugging.

---

## Token Economics

### Current Architecture (25 Tools)
```
Average tool definition: 200-300 tokens
Total per request: 5,000-7,500 tokens
Over 10-turn conversation: 50,000-75,000 tokens
```

### Proposed Architecture (6 Tools)
```
Average tool definition: 200-300 tokens
Total per request: 1,200-1,800 tokens
Over 10-turn conversation: 12,000-18,000 tokens

SAVINGS: ~62,000 tokens (75% reduction)
```

---

## Implementation Notes

### Parameter Standardization
**Current Issue:** Inconsistent parameter names across tools.

| Tool | Current Params | Should Be |
|------|----------------|-----------|
| `revenue_summary` | `date_from`, `date_to` | ✅ Correct |
| `sales_rep_revenue_report` | `date_from`, `date_to` | ✅ Correct |
| `invoice_list_sales` | `date_from`, `date_to` | ✅ Correct |

**Good news:** Already standardized! No changes needed.

### Response Format
**Current:** Markdown-formatted text (✅ CORRECT for MCP)

Example:
```markdown
# Revenue Summary (PAID INVOICES ONLY)

**Period**: 2026-01-01 to 2026-01-24
**Paid Invoices**: 16

## Revenue Calculation:
**Revenue Before Tax**: Rp 92,823,250.00
**Tax (PPN)**: Rp 8,678,450.00
**Revenue After Tax**: Rp 101,501,700.00
```

**Status:** No changes needed. Markdown is the correct format for MCP tools.

---

## Business Intelligence Capabilities

### Currently Supported Queries

#### ✅ Revenue Analysis
- "What was revenue last month?"
- "Show revenue for last week"
- "Daily revenue for the past 2 days"

#### ✅ Sales Rep Performance
- "Who are our sales representatives?"
- "Show revenue by sales rep for this month"
- "Which sales rep has the highest revenue?"

#### ✅ Invoice Lifecycle
- "How many invoices were created this month?"
- "How many invoices are paid?"
- "Show outstanding invoices"

#### ✅ Customer Analysis
- "Who is our biggest customer this month?"
- "Top 10 customers by revenue"
- "Show transaction history for customer X"

#### ⚠️ Commission Calculation (Partial)
- ✅ Revenue data per sales rep
- ❌ Sales targets (not in API)
- ❌ Commission formula (not implemented)

**Next Steps for Commissions:**
1. Add sales target tracking (manual input or separate table)
2. Implement commission formula logic
3. Create commission_calculator tool

---

## Data Quality & Completeness

### ✅ Excellent Data Coverage
- **Invoice fields:** 75+ fields available
- **Nested relationships:** Contact, sales_person, warehouse, payment terms
- **Financial precision:** Separate before-tax and after-tax amounts
- **Date tracking:** trans_date, due_date, payment_date, paid_date
- **Status tracking:** Clear status_id (1/2/3) for payment states

### ✅ No Missing Critical Data
All fields needed for current business queries are present:
- ✅ Revenue amounts (subtotal, total_tax, amount_after_tax)
- ✅ Sales rep identification (sales_id, sales_person.name)
- ✅ Customer details (contact.name, contact.company)
- ✅ Payment status (status_id, due_days)
- ✅ Date ranges for filtering

---

## Recommendations

### Immediate Actions (Priority Order)
1. **✅ Complete:** API is working, full data available
2. **Next:** Refactor to 6 consolidated tools (75% token savings)
3. **Then:** Build commission calculator with target tracking
4. **Finally:** Add remaining entities (orders, deliveries) as needed

### Tool Consolidation Benefits
- **Performance:** 75% reduction in token overhead
- **UX:** Clearer tool selection (6 entities vs 25 operations)
- **Maintenance:** Simpler codebase, easier to extend
- **Cost:** Significant token cost savings at scale

### When to Add More Tools
Only add new tools when:
1. Real business query cannot be satisfied by existing 6 tools
2. New tool serves a distinct business entity (not operation variant)
3. Usage justifies the token overhead (~200-300 tokens/request)

---

## Appendix: Full Endpoint Reference

### Invoices
- `GET /finance/invoices` - List sales invoices
- `GET /finance/invoices/{id}` - Invoice details
- `GET /finance/invoices/totals` - Invoice totals

### Reports
- `GET /reportings/activity-team` - Activity team report
- `GET /reportings/profit-loss` - Profit & loss
- `GET /reportings/sales-by-contact` - Sales by customer

### Products
- `GET /finance/products` - List products
- `GET /finance/products/{id}` - Product details

### Contacts
- `GET /finance/contacts` - List contacts
- `GET /finance/contacts/{id}` - Contact details
- `GET /finance/contacts/{id}/transactions` - Contact transactions

### Supporting Data
- `GET /finance/units` - Product units
- `GET /finance/tags` - Transaction tags
- `GET /warehouses` - Warehouse list

---

**Document Version:** 1.0.0
**Last Validated:** January 24, 2026 with real API calls
**Status:** Production-ready, consolidation recommended
