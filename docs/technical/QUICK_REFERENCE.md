# Kledo API - Quick Reference Guide

Quick lookup for common operations and data structures.

---

## 🔥 Most Used Tools (Based on Real Usage)

### Revenue Summary
```python
# Get revenue for any period
revenue_summary(date_from="2026-01-01", date_to="2026-01-31")

# Shortcuts available
revenue_summary(date_from="this_month")
revenue_summary(date_from="last_month")
revenue_summary(date_from="this_year")
```

**Returns:**
- Revenue Before Tax
- Tax Amount (PPN)
- Revenue After Tax
- Number of paid invoices
- Average invoice value

---

### Invoice Listing
```python
# All invoices this month
invoice_list_sales(
    date_from="2026-01-01",
    date_to="2026-01-31"
)

# Only paid invoices
invoice_list_sales(
    date_from="2026-01-01",
    date_to="2026-01-31",
    status="paid"  # or "unpaid", "partial"
)
```

---

### Sales Rep Performance
```python
# Get all sales reps
sales_rep_list()

# Revenue by sales rep
sales_rep_revenue_report(
    date_from="2026-01-01",
    date_to="2026-01-31"
)
```

**Returns for each rep:**
- Sales rep name
- Total revenue (before/after tax)
- Number of invoices
- Average invoice value

---

### Top Customers
```python
# Get top 10 customers by revenue
customer_revenue_ranking(
    date_from="2026-01-01",
    date_to="2026-01-31",
    top_n=10
)
```

**Returns:**
- Customer name & company
- Total revenue
- Number of invoices
- Average invoice value

---

## 📊 Invoice Data Structure

### Key Financial Fields
```python
{
    # Amounts (IDR)
    'subtotal': 16320000,           # Before tax
    'total_tax': 1795200,            # Tax amount
    'amount_after_tax': 18115200,    # After tax

    # Status
    'status_id': 3,                  # 1=Unpaid, 2=Partial, 3=Paid
    'due': 0,                        # Outstanding amount
    'due_days': 0,                   # Days overdue

    # Dates
    'trans_date': '2026-01-23',
    'due_date': '2026-01-23',
    'paid_date': '2026-01-23',

    # People
    'sales_person': {
        'id': 230701,
        'name': 'Teuku Muda Rabian Hussein'
    },
    'contact': {
        'id': 489,
        'name': 'Tahroni Arifin',
        'company': 'PT. RANGKA RUANG INDONESIA'
    }
}
```

---

## 🧮 Common Calculations

### Total Revenue
```python
# Revenue before tax
revenue_before_tax = sum(inv['subtotal'] for inv in invoices if inv['status_id'] == 3)

# Revenue after tax
revenue_after_tax = sum(inv['amount_after_tax'] for inv in invoices if inv['status_id'] == 3)
```

### Group by Sales Rep
```python
from collections import defaultdict

rep_revenue = defaultdict(lambda: {'total': 0, 'count': 0, 'name': ''})

for invoice in paid_invoices:
    sales_id = invoice['sales_id']
    rep_revenue[sales_id]['total'] += invoice['amount_after_tax']
    rep_revenue[sales_id]['count'] += 1
    rep_revenue[sales_id]['name'] = invoice['sales_person']['name']
```

### Group by Customer
```python
customer_revenue = defaultdict(lambda: {'total': 0, 'count': 0, 'name': ''})

for invoice in paid_invoices:
    contact_id = invoice['contact_id']
    customer_revenue[contact_id]['total'] += invoice['amount_after_tax']
    customer_revenue[contact_id]['count'] += 1
    customer_revenue[contact_id]['name'] = invoice['contact']['name']

# Sort by revenue
top_customers = sorted(customer_revenue.items(), key=lambda x: x[1]['total'], reverse=True)
```

---

## ⚡ Status Codes

### Invoice Status
```python
STATUS_UNPAID = 1      # Belum Dibayar
STATUS_PARTIAL = 2     # Dibayar Sebagian
STATUS_PAID = 3        # Lunas

# Get outstanding invoices
outstanding = [inv for inv in invoices if inv['status_id'] in [STATUS_UNPAID, STATUS_PARTIAL]]

# Get paid invoices only
paid = [inv for inv in invoices if inv['status_id'] == STATUS_PAID]
```

---

## 📅 Date Shortcuts

### Supported Shortcuts
```python
date_from="this_month"    # Current month (Jan 1 - Jan 24)
date_from="last_month"    # Previous month (Dec 1 - Dec 31)
date_from="this_year"     # Current year (Jan 1 - today)
```

### Custom Date Ranges
```python
# Format: YYYY-MM-DD
date_from="2026-01-01"
date_to="2026-01-31"
```

---

## 🔍 Filtering & Search

### By Status
```python
# Paid only
invoice_list_sales(status="paid")

# Unpaid only
invoice_list_sales(status="unpaid")

# Partially paid
invoice_list_sales(status="partial")
```

### By Date Range
```python
invoice_list_sales(
    date_from="2026-01-01",
    date_to="2026-01-31"
)
```

### By Customer
```python
invoice_list_sales(contact_id=489)
```

---

## 💡 Real Query Examples

### "What was revenue last month?"
```python
revenue_summary(date_from="last_month")
```

### "Show unpaid invoices"
```python
outstanding_receivables(status_id=1)  # 1 = Unpaid only
```

### "Top 5 customers this month"
```python
customer_revenue_ranking(
    date_from="this_month",
    top_n=5
)
```

### "Sales rep performance this month"
```python
sales_rep_revenue_report(date_from="this_month")
```

### "How many invoices were paid this week?"
```python
invoice_list_sales(
    date_from="2026-01-17",  # 7 days ago
    date_to="2026-01-24",     # today
    status="paid"
)
```

---

## 🎯 Commission Calculation (Current Capability)

### Available Data
```python
# Get revenue per sales rep
sales_rep_revenue_report(date_from="this_month")

# Returns:
{
    'sales_rep_name': 'Teuku Muda Rabian Hussein',
    'total_revenue_before_tax': 45000000,
    'total_revenue_after_tax': 49500000,
    'invoice_count': 8,
    'average_invoice': 6187500
}
```

### Missing for Full Commission Calc
- ❌ Sales targets per rep
- ❌ Commission percentage/tiers
- ❌ Target achievement percentage

**Next Steps:** Implement target tracking + commission formula.

---

## 🚀 Performance Tips

### Use Caching
Cache is enabled by default (TTL: 30 minutes). To bypass:
```python
client.list_invoices(force_refresh=True)
```

### Pagination
```python
# Get large datasets
invoice_list_sales(
    per_page=100,  # Max items per page
    page=1          # Page number
)
```

### Filter Early
Always filter by date range and status to reduce data transfer:
```python
# Good - specific filters
invoice_list_sales(
    date_from="2026-01-01",
    date_to="2026-01-31",
    status="paid"
)

# Avoid - fetching everything
invoice_list_sales()  # Gets all invoices (slow!)
```

---

## 🔧 Debugging

### Test Connection
```python
utility_test_connection()
```

### Check Cache Stats
```python
utility_get_cache_stats()
```

### Clear Cache
```python
utility_clear_cache()
```

---

## 📈 Token Usage Guide

### Current (25 Tools)
- ~250 tokens per tool definition
- 25 tools = ~6,250 tokens per request
- 10-turn conversation = ~62,500 tokens

### After Consolidation (6 Tools)
- ~250 tokens per tool definition
- 6 tools = ~1,500 tokens per request
- 10-turn conversation = ~15,000 tokens

**Savings: 47,500 tokens (76%) per 10-turn conversation**

---

**Quick Tip:** Start with `revenue_summary(date_from="this_month")` - it's the most used query and returns comprehensive financial data!
