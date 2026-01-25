================================================================================
KLEDO API - REVENUE REPORTING FIELD MAPPING
Generated: 2026-01-22 20:12:57
================================================================================

✓ Authentication: SUCCESS

Fetching data from endpoints:
  ✓ invoices/list - 3 samples fetched
  ✓ purchase_invoices/list - 3 samples fetched
  ✓ products/list - 3 samples fetched
  ✓ contacts/list - 3 samples fetched


================================================================================
📊 SALES INVOICES
================================================================================

Customer invoices for revenue calculation

Available Fields in API Response:
--------------------------------------------------------------------------------
Total fields: 75

  id                             = 13335
  business_tran_id               = 13289
  trans_type_id                  = 5
  trans_date                     = 2026-01-19
  due_date                       = 2026-01-19
  contact_id                     = 430
  status_id                      = 3
  ref_number                     = INV/26/JAN/01153
  amount                         = 4410000
  amount_after_tax               = 4410000
  due                            = 0
  bank_statement_id              = null
  bank_account_id                = null
  balance                        = null
  position                       = null
  pay_later                      = False
  pay_from_finance_account_id    = null
  payment_id                     = null
  include_tax                    = True
  term_id                        = 5
  attachment                     = []
  memo                           = Villa Mas Nusa Indah - 2 - 169
  desc                           = 
  tax                            = []
  warehouse_id                   = 1
  discount_percent               = 0
  discount_amount                = 0
  additional_discount_percent    = 0
  additional_discount_amount     = 0
  total_tax                      = 0
  subtotal                       = 4410000
  shipping_cost                  = 0
  shipping_date                  = null
  shipping_comp_id               = null
  shipping_tracking              = null
  sub_business_tran_id           = null
  delivery_ids                   = null
  witholding_percent             = 0
  witholding_amount              = 0
  witholding_account_id          = null
  owner_id                       = 218933
  sales_id                       = 352181
  currency_id                    = 0
  currency_source_id             = 0
  currency_rate                  = 1
  payment_date                   = 2026-01-19
  paid_date                      = 2026-01-19
  contact_shipping_address_id    = null
  amount_after_tax_ori           = null
  amount_ori                     = null
  local_id                       = null
  outlet_id                      = null
  invoice_type_id                = null
  payment_type_id                = null
  pos_shift_id                   = null
  related_id                     = null
  related_type                   = null
  is_stamped                     = False
  stamp_serial_number            = null
  source                         = 0
  source_id                      = null
  created_at                     = 2026-01-19
  updated_at                     = 2026-01-19
  contact                        = {'id': 430, 'name': 'Adil', 'company': None, 'npwp': None}
  termin                         = {'id': 5, 'name': 'Cash Before Delivery'}
  related                        = null
  warehouse                      = {'id': 1, 'name': 'Coating dan Cat'}
  sales_person                   = {'id': 352181, 'name': 'Elmo Abu Abdillah'}
  attachment_exists              = False
  tags                           = [{'id': 1, 'name': 'Penjualan Material', 'color': '#000000'}
  print_status                   = Sudah
  order_number                   = SO/26/JAN/00836
  due_days                       = 0
  qty                            = 13
  payment_accounts               = [{'id': 1507, 'name': 'Mandiri Main 6667', 'name_id': 'Mandi

────────────────────────────────────────────────────────────────────────────────

Mapped Fields (for revenue reporting):
--------------------------------------------------------------------------------
✓ ref_number                → Invoice Number (e.g., INV/26/JAN/00123)
   Sample: INV/26/JAN/01153

✓ trans_date                → Transaction Date (when the invoice was created)
   Sample: 2026-01-19

✓ contact.name              → Customer Name
   Sample: Adil

✓ contact.id                → Customer ID (for grouping by customer)
   Sample: 430

✓ amount_after_tax          → Total Invoice Amount (including tax)
   Sample: 4410000

✓ due                       → Amount Still Owed (unpaid balance)
   Sample: 0

✓ status_id                 → Invoice Status (1=Draft, 2=Pending, 3=Paid, 4=Partial, 5=Overdue)
   Sample: 3

✓ sales_person.id           → Sales Representative ID
   Sample: 352181

✓ sales_person.name         → Sales Representative Name
   Sample: Elmo Abu Abdillah

✓ subtotal                  → Subtotal Before Tax
   Sample: 4410000

✓ total_tax                 → Total Tax Amount
   Sample: 0

✓ tax                       → Tax Details (rate and amount)
   Sample: []


💡 Revenue Calculation:
   Use 'amount_after_tax' for total revenue. Filter by 'status_id=3' (Paid) for confirmed revenue.


================================================================================
📊 PURCHASE INVOICES
================================================================================

Vendor bills for expense/cost calculation

Available Fields in API Response:
--------------------------------------------------------------------------------
Total fields: 23

  ref_number                     = PI/26/JAN/01174
  contact_id                     = 279
  trans_date                     = 2026-01-21
  due_date                       = 2026-02-20
  status_id                      = 1
  due                            = 4225936.5
  amount_after_tax               = 4225936.5
  id                             = 13362
  additional_discount_amount     = 0
  currency_rate                  = 1
  currency_id                    = 0
  shipping_cost                  = 0
  shipping_date                  = null
  payment_date                   = null
  paid_date                      = null
  trans_type_id                  = 3
  related_id                     = null
  related_type                   = null
  contact                        = {'id': 279, 'name': 'Dani Prasetyo', 'email': None, 'phone':
  additional_discounts           = null
  total_additional_discounts     = 0
  products                       = [{'id': 318, 'name': 'KANSAI FTALIT PERMANENT RED', 'qty': 3
  amount                         = 0

────────────────────────────────────────────────────────────────────────────────

Mapped Fields (for revenue reporting):
--------------------------------------------------------------------------------
✓ ref_number                → Purchase Invoice Number
   Sample: PI/26/JAN/01174

✓ trans_date                → Transaction Date
   Sample: 2026-01-21

✓ contact.name              → Vendor Name
   Sample: Dani Prasetyo

✓ contact.id                → Vendor ID
   Sample: 279

✓ amount_after_tax          → Total Bill Amount (including tax)
   Sample: 4225936.5

✓ due                       → Amount Still Owed to Vendor
   Sample: 4225936.5

✓ status_id                 → Bill Status (1=Draft, 2=Pending, 3=Paid, etc.)
   Sample: 1

✓ amount                    → Amount Before Discounts
   Sample: 0


💡 Revenue Calculation:
   Use 'amount_after_tax' for total expenses/costs.


================================================================================
📊 PRODUCTS
================================================================================

Product catalog with pricing

Available Fields in API Response:
--------------------------------------------------------------------------------
Total fields: 16

  id                             = 213
  name                           = Alat Bantu - Bongkar/Pasang Scaffolding
  code                           = SKU/CD/00208
  base_price                     = 0
  price                          = 85000000
  qty                            = 0
  is_track                       = False
  unit_id                        = 10
  bundle_type_id                 = 0
  variant_type_id                = 0
  sn_type                        = null
  pos_product_category_id        = 9
  avg_base_price                 = 0
  is_archive                     = 0
  unit                           = {'id': 10, 'name': 'LS'}
  warehouse_qty                  = []

────────────────────────────────────────────────────────────────────────────────

Mapped Fields (for revenue reporting):
--------------------------------------------------------------------------------
✓ name                      → Product Name
   Sample: Alat Bantu - Bongkar/Pasang Scaffolding

✓ code                      → Product SKU/Code
   Sample: SKU/CD/00208

✓ price                     → Selling Price per Unit
   Sample: 85000000

✓ base_price                → Base/Cost Price per Unit
   Sample: 0

✓ qty                       → Current Stock Quantity
   Sample: 0

✓ avg_base_price            → Average Cost Price
   Sample: 0


💡 Revenue Calculation:
   Use 'price' for revenue per unit. Calculate profit margin: (price - base_price) / price


================================================================================
📊 CONTACTS (CUSTOMERS & VENDORS)
================================================================================

Customer and vendor information

Available Fields in API Response:
--------------------------------------------------------------------------------
Total fields: 22

  company                        = null
  name                           = KLEDO
  payable                        = 0.00000
  receivable                     = 0.00000
  id                             = 2
  local_id                       = 9d311a4e-f0ea-4044-a2be-eb64a7ab447e
  receivable_account_id          = 21
  payable_account_id             = 81
  is_archive                     = 0
  type_id                        = 1
  group_id                       = 2
  finance_term_id                = null
  type_ids                       = [1]
  edit_address                   = null
  group                          = {'id': 2, 'code': None, 'name': 'Software License', 'is_acti
  term                           = null
  finance_contact_emails         = []
  country                        = null
  province                       = null
  city                           = null
  district                       = null
  village                        = null

────────────────────────────────────────────────────────────────────────────────

Mapped Fields (for revenue reporting):
--------------------------------------------------------------------------------
✓ name                      → Contact Name
   Sample: KLEDO

✗ company                   → Company Name
   Sample: N/A

✓ type_id                   → Contact Type ID
   Sample: 1

✓ type_ids                  → Multiple Type IDs
   Sample: [1]

✓ receivable                → Total Amount Customer Owes Us
   Sample: 0.00000

✓ payable                   → Total Amount We Owe Vendor
   Sample: 0.00000


💡 Revenue Calculation:
   Use 'receivable' to see outstanding customer payments.


================================================================================
REVENUE REPORT RECOMMENDATIONS
================================================================================

1. Annual Revenue Report:
   - Endpoint: GET /finance/invoices
   - Filters: status_id=3 (Paid only), date_from, date_to
   - Sum: amount_after_tax
   - Group by: trans_date (by month), sales_person.id (by rep)

2. Monthly Revenue Report:
   - Same as annual, filter date_from/date_to to specific month
   - Group by: trans_date (by day)

3. Weekly Revenue Report:
   - Filter to 7-day period
   - Group by: trans_date (daily breakdown)

4. Sales Representative Performance:
   - Group invoices by: sales_person.id
   - Calculate: SUM(amount_after_tax), COUNT(invoices), COUNT(DISTINCT contact.id)
   - Show: Revenue, Invoice count, Customer count per rep

5. Customer Revenue Analysis:
   - Group invoices by: contact.id
   - Calculate: Total revenue per customer, Average invoice value
   - Identify: Top customers by revenue

6. Product Revenue (requires invoice line items):
   - Need to fetch invoice details to get line items
   - Join with products for profit margin calculation

7. Profit Analysis:
   - Revenue: SUM of invoices.amount_after_tax (status_id=3)
   - Costs: SUM of purchase_invoices.amount_after_tax
   - Profit: Revenue - Costs
   - Margin: (Profit / Revenue) × 100

8. Outstanding Receivables:
   - Use: invoices.due field
   - Filter: status_id IN (2,4,5) for unpaid/partial/overdue

Key Fields Summary:
------------------
For Revenue: invoices.amount_after_tax (filter status_id=3)
For Costs: purchase_invoices.amount_after_tax
For Profit Margin: products.price vs products.base_price
For AR/AP: contacts.receivable and contacts.payable
For Sales Rep: sales_person.id and sales_person.name
For Grouping: trans_date (by period), contact.id (by customer)
    

================================================================================
FIELD MAPPING STATUS
================================================================================

✓ All critical fields for revenue reporting are available in the API
✓ Invoice data includes sales representative information
✓ Contact data includes receivables and payables
✓ Product data includes both selling price and cost price
✓ Date fields are in YYYY-MM-DD format for easy grouping

Note: Tax field is 'total_tax' not 'tax_amount' in the actual API response.
    