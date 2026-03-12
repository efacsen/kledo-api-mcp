# Choosing Between Tools

When multiple tools seem applicable, this page helps you pick the right one. Each section explains tool overlaps and when to use each option.

!!! info "When to Read This"
    Consult this page when:

    - The [disambiguation matrix](disambiguation.md) shows "Context-dependent" confidence
    - You're unsure between similar-sounding tools
    - You want to understand the difference between list vs. summary tools

---

## Choosing Between Sales Tools

### invoice_list (type="sales") vs financial_summary (type="sales")

Both tools show sales data, but they serve different purposes.

| Aspect | `invoice_list` (type="sales") | `financial_summary` (type="sales") |
|--------|-------------------------------|-------------------------------------|
| **Returns** | Individual invoice records | Aggregated totals by customer |
| **Grouping** | Flat list | Ranked by revenue |
| **Detail level** | Each invoice with status | Customer totals only |
| **Use case** | Finding specific invoices | Analyzing customer performance |

**Use `invoice_list` with `type="sales"` when:**

- You need to see specific invoice details (invoice number, items, status)
- You want to filter by invoice status (draft, pending, paid)
- You need to find unpaid or overdue invoices
- The user is asking about a particular invoice or date range

**Use `financial_summary` with `type="sales"` when:**

- You want to see top customers ranked by revenue
- You need total sales figures for a period
- You're comparing customer performance
- The user asks "Who are my best customers?"

---

### invoice_list (type="sales") vs invoice_summarize (view="totals")

Both provide sales invoice information, but at different aggregation levels.

| Aspect | `invoice_list` (type="sales") | `invoice_summarize` (view="totals") |
|--------|-------------------------------|--------------------------------------|
| **Returns** | List of invoices | Summary numbers only |
| **Detail** | Individual records | Totals (count, amount, paid, outstanding) |
| **Data volume** | Potentially large | Single summary object |

**Use `invoice_list` with `type="sales"` when:**

- You need to see individual invoice records
- You want to browse or search invoices
- You need invoice numbers or line items

**Use `invoice_summarize` with `view="totals"` when:**

- You only need aggregate numbers (total amount, count)
- You want to know total outstanding or overdue amounts
- You're answering "How many invoices?" or "What's my total receivables?"

---

## Choosing Between Contact Tools

### contact_list vs financial_summary (type="sales") for customer questions

Both can answer "Who are my customers?" but from different angles.

| Aspect | `contact_list` | `financial_summary` (type="sales") |
|--------|----------------|-------------------------------------|
| **Returns** | Contact information | Sales performance data |
| **Ranking** | Alphabetical/search order | By revenue |
| **Data type** | Name, email, phone | Sales amount, invoice count |

**Use `contact_list` when:**

- You're looking up a customer by name or email
- You need contact information (address, phone)
- You want to find a specific contact ID

**Use `financial_summary` with `type="sales"` when:**

- You want to know top customers by revenue
- You're analyzing sales performance by customer
- The user asks "Who are my biggest customers?"

---

### contact_get (view="transactions") vs invoice_list (type="sales") with contact_id

Both show a customer's transaction history, but with different scope.

| Aspect | `contact_get` (view="transactions") | `invoice_list` (type="sales") + contact_id |
|--------|--------------------------------------|---------------------------------------------|
| **Scope** | All transaction types | Only sales invoices |
| **Includes** | Invoices, payments, credits, adjustments | Invoices only |
| **Summary** | Yes (total count, amount) | No built-in summary |

**Use `contact_get` with `view="transactions"` when:**

- You want the full transaction history (invoices AND payments AND credits)
- You need to see all interactions with a customer
- The user asks "What's the history with this customer?"

**Use `invoice_list` with `type="sales"` and `contact_id` when:**

- You only want sales invoices for that customer
- You need to filter by invoice status
- The user specifically asks about invoices, not all transactions

---

## Choosing Between Product Tools

### product_list vs product_get (with sku param)

Both find products, but optimized for different lookup patterns.

| Aspect | `product_list` | `product_get` (with `sku` param) |
|--------|----------------|-----------------------------------|
| **Lookup method** | Name, description, or browse | Exact SKU match |
| **Results** | Multiple products | Single product |
| **Inventory** | Optional (use include_inventory) | Included |

**Use `product_list` when:**

- You're browsing the product catalog
- You're searching by product name or description
- You don't have the exact SKU
- The user says "Find products like..."

**Use `product_get` with `sku` param when:**

- You have the exact SKU/product code
- You want a quick single-product lookup
- The user provides a specific product code

---

## Choosing Between Order and Invoice Tools

### order_list (type="sales") vs invoice_list (type="sales")

Orders and invoices represent different stages in the sales process.

| Aspect | `order_list` (type="sales") | `invoice_list` (type="sales") |
|--------|------------------------------|--------------------------------|
| **Stage** | Pre-billing (quotations, confirmed orders) | Post-billing (bills sent) |
| **Status** | Draft, Confirmed, Delivered | Draft, Pending, Paid, Overdue |
| **Payment tracking** | No payment info | Tracks payments |

**Use `order_list` with `type="sales"` when:**

- You're looking at confirmed orders not yet invoiced
- You want to see what's in the pipeline before billing
- The user asks about orders or quotations

**Use `invoice_list` with `type="sales"` when:**

- You're looking at billed transactions
- You need payment status (paid, pending, overdue)
- The user asks about invoices or receivables

!!! note "Workflow Tip"
    In Kledo, the typical flow is: **Order** (quotation) → **Invoice** (bill) → **Delivery** (shipment) → **Payment** (settled)

---

## Choosing Between Delivery Tools

### delivery_list vs delivery_get (view="pending")

Both show deliveries, but with different filters.

| Aspect | `delivery_list` | `delivery_get` (view="pending") |
|--------|-----------------|----------------------------------|
| **Scope** | All deliveries (filterable) | Only pending/unshipped |
| **Parameters** | date_from, date_to, status_id | None |
| **Use case** | Browse history | Quick action list |

**Use `delivery_list` when:**

- You want to see all deliveries for a date range
- You need to filter by specific status
- You're reviewing delivery history

**Use `delivery_get` with `view="pending"` when:**

- You want to see what needs to be shipped today
- You're answering "What deliveries are pending?"
- You need a quick operational checklist

---

## Summary Decision Tree

```
Is the user asking about...

Revenue/Sales totals?
├── By customer? → financial_summary (type="sales")
├── Total amounts? → invoice_summarize (view="totals")
└── Specific invoices? → invoice_list (type="sales")

Customer information?
├── Contact details? → contact_list or contact_get (view="detail")
├── Top customers by revenue? → financial_summary (type="sales")
└── Transaction history? → contact_get (view="transactions")

Product information?
├── Have exact SKU? → product_get (with sku param)
└── Searching by name? → product_list

Invoice vs Order?
├── Already billed? → invoice_list (type="sales")
└── Not yet invoiced? → order_list (type="sales")

Pending items?
├── Overdue invoices? → invoice_summarize (view="totals")
└── Pending deliveries? → delivery_get (view="pending")
```

---

## See Also

- [Find the Right Tool](disambiguation.md) - Business question to tool matrix
- [Tool Catalog](index.md) - Complete tool reference
