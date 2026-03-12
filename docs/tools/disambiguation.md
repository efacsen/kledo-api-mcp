# Find the Right Tool

This page helps you find the correct tool for your business question. Use the matrix below to map natural language queries to the appropriate MCP tool.

## How to Read This Matrix

| Column | Description |
|--------|-------------|
| **Business Question** | Natural language query in English and Indonesian |
| **Recommended Tool** | Primary tool to use for this question |
| **Confidence** | **Definitive** = Only one tool makes sense; **Context-dependent** = May need more information |
| **Parameters** | Key parameters to provide |
| **Alternative** | Another tool that could work, with note on when to use it |

!!! tip "For AI Agents"
    - **Definitive** confidence means you can call the tool directly
    - **Context-dependent** means ask the user for clarification first
    - Check the [Choosing Between Tools](choosing.md) page for detailed overlap explanations

---

## Reporting Queries

Questions about financial summaries and trends.

| Business Question | Recommended Tool | Confidence | Parameters | Alternative |
|-------------------|------------------|------------|------------|-------------|
| What is my revenue? / Berapa pendapatan saya? | `financial_summary` (type="sales") | Definitive | date_from, date_to | `invoice_summarize` (view="totals") (if need paid vs outstanding breakdown) |
| What are my expenses? / Berapa pengeluaran saya? | `financial_summary` (type="purchase") | Definitive | date_from, date_to | - |
| Show my sales trends / Tunjukkan tren penjualan | `financial_summary` (type="sales") | Context-dependent | date_from, date_to | `invoice_list` (type="sales") (if need individual invoice details) |
| What's my cash balance? / Berapa saldo kas saya? | `financial_balances` | Definitive | (none) | - |

---

## Data Lookup Queries

Questions about finding specific records.

| Business Question | Recommended Tool | Confidence | Parameters | Alternative |
|-------------------|------------------|------------|------------|-------------|
| Show invoice #123 / Tampilkan faktur #123 | `invoice_get` | Definitive | invoice_id | - |
| Find customer X / Cari pelanggan X | `contact_list` | Definitive | search | `contact_get` (view="detail") (if you have contact_id) |
| What's the price of product Y? / Berapa harga produk Y? | `product_list` | Context-dependent | search | `product_get` (with sku param) (if you have exact SKU) |
| Show order details / Tampilkan detail pesanan | `order_get` | Definitive | order_id | `invoice_get` (if it's an invoice, not order) |

---

## Analytical Queries

Questions about rankings, comparisons, and history.

| Business Question | Recommended Tool | Confidence | Parameters | Alternative |
|-------------------|------------------|------------|------------|-------------|
| Who are my top customers? / Siapa pelanggan terbesar saya? | `financial_summary` (type="sales") | Definitive | date_from, date_to | - |
| What are my best selling products? / Produk apa yang paling laris? | - | Context-dependent | - | No direct tool available. Use `invoice_list` (type="sales") and aggregate by product |
| How much do I owe vendor X? / Berapa hutang saya ke vendor X? | `contact_get` (view="detail") | Context-dependent | contact_id | `financial_summary` (type="purchase") (for total purchases from vendor) |
| What's customer X's transaction history? / Apa riwayat transaksi pelanggan X? | `contact_get` (view="transactions") | Definitive | contact_id | `invoice_list` (type="sales") (if only want invoices, not all transactions) |

---

## Status/Health Queries

Questions about outstanding items and pending tasks.

| Business Question | Recommended Tool | Confidence | Parameters | Alternative |
|-------------------|------------------|------------|------------|-------------|
| Any overdue invoices? / Ada faktur jatuh tempo? | `invoice_summarize` (view="totals") | Definitive | (none) | `invoice_list` (type="sales") with status_id filter (to see specific invoices) |
| Pending deliveries? / Pengiriman yang tertunda? | `delivery_get` (view="pending") | Definitive | (none) | `delivery_list` with status filter |
| Total outstanding receivables? / Total piutang? | `invoice_summarize` (view="totals") | Definitive | (none) | - |

---

## Quick Reference by Entity

### Invoices
- **List invoices**: `invoice_list` (with `type="sales"` or `type="purchase"`)
- **Get single invoice**: `invoice_get`
- **Get totals/summary**: `invoice_summarize` (with `view="totals"`, `view="by_customer"`, or `view="by_vendor"`)

### Orders
- **List orders**: `order_list` (with `type="sales"` or `type="purchase"`)
- **Get single order**: `order_get`

### Contacts (Customers/Vendors)
- **Search contacts**: `contact_list`
- **Get contact details**: `contact_get` (with `view="detail"`)
- **Get transaction history**: `contact_get` (with `view="transactions"`)

### Products
- **Search products**: `product_list`
- **Get product by SKU**: `product_get` (with `sku` param)
- **Get product details**: `product_get`

### Deliveries
- **List deliveries**: `delivery_list`
- **Get pending shipments**: `delivery_get` (with `view="pending"`)
- **Get delivery details**: `delivery_get` (with `view="detail"`)

### Finance
- **Sales summary by customer**: `financial_summary` (with `type="sales"`)
- **Purchase summary by vendor**: `financial_summary` (with `type="purchase"`)
- **Bank balances**: `financial_balances`
- **Team activity**: `financial_activity`

---

## See Also

- [Choosing Between Tools](choosing.md) - Detailed guidance on overlapping tools
- [Tool Catalog](index.md) - Complete tool reference
