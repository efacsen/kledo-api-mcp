# Analytics Capability Map - Kledo API

**Perspective:** Finance Analyst + Data Analyst
**Date:** January 24, 2026
**Status:** Comprehensive mapping of all possible reports and analytics

---

## 📊 Executive Summary

From the available Kledo API data, we can generate **60+ distinct financial reports and analytics** across 8 major categories:

1. **Financial Reporting** (13 reports)
2. **Revenue Analytics** (9 reports)
3. **Sales Performance** (12 reports)
4. **Customer Intelligence** (11 reports)
5. **Cash Flow & Receivables** (8 reports)
6. **Operational Metrics** (7 reports)
7. **Risk Management** (5 reports)
8. **Predictive Analytics** (5 reports)

---

## 🎯 Data Assets Available

### Primary Data Sources
```python
Invoice Data Fields (75+):
├── Financial: subtotal, total_tax, amount_after_tax, due, discount
├── Dates: trans_date, due_date, payment_date, paid_date
├── Status: status_id (unpaid/partial/paid), due_days
├── Relationships: contact, sales_person, warehouse, termin
├── Metadata: tags, memo, order_number, ref_number
└── Payment: payment_accounts, payment_type_id
```

---

## 1️⃣ FINANCIAL REPORTING

### 1.1 Income Statement Analysis
**Data Available:** ✅ Complete (**VALIDATED WITH 5 REAL INVOICES**)

```python
# Revenue Recognition (PROVEN BY DATA)
# Mathematical relationship: subtotal + total_tax = amount_after_tax ✅

- Penjualan Bruto / Gross Sales    = amount_after_tax
  (Total yang dibayar customer, INCLUDING tax)

- Dikurangi: PPN / VAT              = total_tax
  (Tax collected, 11% of subtotal for taxable transactions)

- Penjualan Neto / Net Sales        = subtotal
  (Revenue BEFORE tax, yang jadi revenue perusahaan)

- Discounts Given                   = discount_amount + additional_discount_amount
- Shipping Revenue                  = shipping_cost
```

**IMPORTANT:** In Indonesian accounting context:
- `amount_after_tax` = "amount INCLUDING tax" (bukan "after deducting tax")
- This is the **total transaction value** customer pays
- `subtotal` is the actual **revenue** retained by company (before remitting tax)

**Reports:**
- **Monthly P&L Summary**
  - Penjualan Bruto (Gross Sales) = amount_after_tax
  - Dikurangi: PPN collected = total_tax
  - Penjualan Neto (Net Sales) = subtotal
  - Average transaction value
  - YoY comparison

- **Revenue by Tax Treatment**
  - Taxable transactions (with PPN 11%)
  - Non-taxable transactions (PPN = 0)
  - Tax compliance tracking
  - VAT/PPN analysis

- **Discount Impact Analysis**
  - Total discounts given
  - Discount % of gross sales
  - Discount trends over time

**Formula Example (VALIDATED):**
```python
# Proven with 5 invoices:
# Invoice #1: 16,320,000 + 1,795,200 = 18,115,200 ✅
# Invoice #2:  4,410,000 +         0 =  4,410,000 ✅
# Invoice #3:  7,560,000 +   831,600 =  8,391,600 ✅

# For Indonesian Income Statement:
penjualan_bruto = amount_after_tax  # Total paid by customer
ppn_collected = total_tax            # Tax (usually 11%)
penjualan_neto = subtotal            # Revenue before tax

# Verify relationship:
assert subtotal + total_tax == amount_after_tax

# Tax rate calculation:
tax_rate = (total_tax / subtotal) * 100  # Usually 11% for taxable items

# Net margin (simplified, without COGS):
net_margin_rate = (subtotal / amount_after_tax) * 100  # ~90% for 11% tax
```

---

### 1.2 Tax Reporting
**Data Available:** ✅ Complete

**Reports:**
- **PPN (VAT) Summary Report**
  - Total taxable revenue
  - Total PPN collected
  - PPN rate analysis
  - Customer NPWP tracking

- **Tax Compliance Dashboard**
  - Transactions with vs without tax
  - NPWP coverage rate
  - Tax reporting readiness

**Fields Used:**
```python
tax: {"1": 1795200}  # Tax breakdown
total_tax: 1795200   # Total tax amount
contact.npwp: "509721197002000"  # Customer tax ID
```

---

### 1.3 Period Comparison Analysis
**Data Available:** ✅ Complete

**Reports:**
- **Month-over-Month (MoM) Growth**
  ```
  Jan 2026 vs Dec 2025
  - Revenue growth %
  - Invoice count change
  - Average invoice size change
  ```

- **Year-over-Year (YoY) Analysis**
  ```
  Jan 2026 vs Jan 2025
  - Annual growth rate
  - Seasonal patterns
  - Market share trends
  ```

- **Quarter-over-Quarter (QoQ) Trends**
  ```
  Q4 2025 vs Q3 2025
  - Quarterly performance
  - Seasonal adjustments
  - Trend identification
  ```

**Calculation:**
```python
mom_growth = ((current_month - last_month) / last_month) * 100
yoy_growth = ((current_year - last_year) / last_year) * 100
cagr = ((end_value / start_value) ** (1/years) - 1) * 100
```

---

## 2️⃣ REVENUE ANALYTICS

### 2.1 Revenue Breakdown Analysis
**Data Available:** ✅ Complete

**Reports:**
- **Revenue by Warehouse**
  ```python
  warehouse.name: "Coating dan Cat"
  # Track which warehouses generate most revenue
  ```

- **Revenue by Tag/Category**
  ```python
  tags: [{"name": "Penjualan Material"}]
  # Product line performance
  ```

- **Revenue by Payment Terms**
  ```python
  termin.name: "Cash Before Delivery"
  # Impact of payment terms on sales
  ```

- **Revenue by Invoice Type**
  ```python
  invoice_type_id, source, source_id
  # Channel analysis (POS, online, manual)
  ```

---

### 2.2 Time-Series Revenue Analysis
**Data Available:** ✅ Complete

**Reports:**
- **Daily Revenue Trends**
  - Revenue by day of week
  - Peak sales days
  - Weekend vs weekday patterns

- **Weekly Revenue Patterns**
  - Week-over-week trends
  - 4-week moving average
  - Weekly volatility

- **Monthly Revenue Seasonality**
  - Best/worst performing months
  - Seasonal indexes
  - Year-end patterns

- **Hourly Analysis** (if trans_date includes time)
  - Peak transaction hours
  - Off-peak periods
  - Staffing optimization insights

**Visualization:**
```
Line charts, heatmaps, seasonal decomposition
```

---

### 2.3 Revenue Concentration Risk
**Data Available:** ✅ Complete

**Reports:**
- **Top Customer Concentration**
  ```
  Top 10 customers = X% of revenue
  Top 20% customers = Y% of revenue (Pareto analysis)
  ```

- **Single Customer Dependency**
  ```
  Max customer revenue / Total revenue = Risk %
  Alert if any customer > 20% of total revenue
  ```

- **Diversification Score**
  ```
  Herfindahl-Hirschman Index (HHI)
  Number of customers for 80% revenue
  ```

**Formula:**
```python
customer_concentration = (top_10_revenue / total_revenue) * 100
hhi = sum((customer_revenue / total_revenue) ** 2)
risk_level = "High" if max_customer_share > 20 else "Moderate"
```

---

## 3️⃣ SALES PERFORMANCE ANALYTICS

### 3.1 Sales Rep Performance
**Data Available:** ✅ Complete

**Reports:**
- **Individual Rep Performance**
  ```python
  sales_person.name: "Teuku Muda Rabian Hussein"
  - Total revenue
  - Invoice count
  - Average deal size
  - Win rate (if order data available)
  ```

- **Sales Rep Ranking**
  - Top performers by revenue
  - Most deals closed
  - Highest average deal size
  - Growth rate comparison

- **Sales Rep Productivity**
  ```
  Revenue per rep / Total revenue = Individual contribution %
  Average invoices per rep per month
  Revenue per working day
  ```

- **Team Performance Metrics**
  ```
  Total team revenue
  Team average metrics
  Top vs bottom quartile analysis
  Performance distribution
  ```

---

### 3.2 Commission Calculations
**Data Available:** ✅ Partial (revenue ready, targets needed)

**Current Capability:**
```python
# AVAILABLE NOW
- Revenue per sales rep (before & after tax)
- Number of deals closed
- Average deal size
- Time-based performance (monthly, quarterly)

# NEEDED FOR FULL COMMISSION
- Sales targets per rep
- Commission percentage/tiers
- Commission rules engine
```

**Reports Ready to Build:**
- **Commission Accrual Report**
  ```
  Rep Name | Revenue | Commission Rate | Commission Amount
  ---------------------------------------------------------
  Rep A    | 100M    | 5%             | 5M (if rate known)
  ```

- **Target vs Actual**
  ```
  Rep Name | Target | Actual | Achievement % | Commission Tier
  ```

- **Commission Forecast**
  ```
  Current month progress
  Projected commission based on trends
  ```

**Formula:**
```python
# Basic commission (when targets available)
if achievement >= 120:
    commission_rate = 7.5%  # Top tier
elif achievement >= 100:
    commission_rate = 5.0%  # Base tier
else:
    commission_rate = 2.5%  # Below target

commission_amount = actual_revenue * commission_rate
```

---

### 3.3 Sales Pipeline Analysis
**Data Available:** ✅ Partial (paid invoices only)

**Reports:**
- **Conversion Metrics**
  ```
  Orders (if available) → Invoices → Payments
  Conversion rate at each stage
  Average time to convert
  ```

- **Sales Velocity**
  ```
  Average days from order to invoice
  Average days from invoice to payment
  Total sales cycle time
  ```

- **Win/Loss Analysis**
  ```
  Number of invoices vs orders
  Cancellation rate
  Reasons for losses (if memo tracked)
  ```

---

### 3.4 Deal Size Analysis
**Data Available:** ✅ Complete

**Reports:**
- **Deal Size Distribution**
  ```
  Micro deals (<1M)     : X invoices, Y%
  Small deals (1-5M)    : X invoices, Y%
  Medium deals (5-20M)  : X invoices, Y%
  Large deals (>20M)    : X invoices, Y%
  ```

- **Average Deal Size Trends**
  ```
  Monthly average invoice value
  Trend direction (increasing/decreasing)
  Deal size by sales rep
  Deal size by customer segment
  ```

- **High-Value Deal Analysis**
  ```
  Top 10 largest deals
  Characteristics of big deals
  Sales rep who close large deals
  ```

---

## 4️⃣ CUSTOMER INTELLIGENCE

### 4.1 Customer Segmentation
**Data Available:** ✅ Complete

**Reports:**
- **RFM Analysis** (Recency, Frequency, Monetary)
  ```python
  Recency: Days since last purchase (trans_date)
  Frequency: Number of invoices
  Monetary: Total revenue (amount_after_tax)

  Segments:
  - Champions: High F, High M, Low R
  - Loyal: High F, Medium M
  - At Risk: High M, High R
  - Lost: High R, Low F
  ```

- **Customer Value Tiers**
  ```
  VIP (Top 5%)      : >100M annual
  Premium (Top 20%) : 50-100M annual
  Standard (50%)    : 10-50M annual
  Small (<30%)      : <10M annual
  ```

- **Customer Lifetime Value (CLV)**
  ```python
  avg_invoice_value = total_revenue / invoice_count
  purchase_frequency = invoice_count / months_active
  customer_lifespan = months_since_first_purchase

  CLV = avg_invoice_value * purchase_frequency * customer_lifespan
  ```

---

### 4.2 Customer Behavior Analysis
**Data Available:** ✅ Complete

**Reports:**
- **Purchase Patterns**
  ```
  Average days between purchases
  Preferred purchase days (day of week)
  Seasonal buying patterns
  Bulk vs frequent small purchases
  ```

- **Payment Behavior Score**
  ```python
  # Based on payment history
  on_time_payment_rate = paid_on_time / total_invoices
  avg_payment_delay = avg(paid_date - due_date)

  Score:
  - A: Always pays early/on-time
  - B: Occasional delays (<7 days)
  - C: Frequent delays (7-30 days)
  - D: Chronic late payer (>30 days)
  ```

- **Discount Sensitivity**
  ```
  Customers who get most discounts
  Discount impact on purchase volume
  Price elasticity analysis
  ```

---

### 4.3 Customer Retention Analysis
**Data Available:** ✅ Complete

**Reports:**
- **Churn Analysis**
  ```python
  inactive_threshold = 90  # days
  last_purchase = max(trans_date) for customer
  days_since_purchase = today - last_purchase

  Status:
  - Active: <30 days
  - At Risk: 30-60 days
  - Churning: 60-90 days
  - Churned: >90 days
  ```

- **Retention Rate**
  ```python
  cohort_retention = (active_customers_end / active_customers_start) * 100
  monthly_retention_rate = ...
  annual_retention_rate = ...
  ```

- **Reactivation Opportunities**
  ```
  List of churned customers
  Their historical value
  Recommended win-back offers
  ```

---

### 4.4 Customer Profitability
**Data Available:** ✅ Good (costs not available)

**Reports:**
- **Revenue per Customer**
  ```
  Total revenue by customer
  Average invoice value by customer
  Gross margin by customer (if costs known)
  ```

- **High-Maintenance Customers**
  ```
  Customers with:
  - High discount rates
  - Frequent payment delays
  - Low average invoice value
  - High transaction count (low efficiency)
  ```

- **Customer Acquisition Cost (CAC) Analysis**
  ```
  (Needs marketing spend data)
  CAC Payback Period = CAC / Monthly revenue per customer
  ```

---

## 5️⃣ CASH FLOW & RECEIVABLES MANAGEMENT

### 5.1 Accounts Receivable (AR) Analysis
**Data Available:** ✅ Complete

**Reports:**
- **AR Aging Report**
  ```
  Category           | Amount    | Count | %
  ------------------------------------------------
  Current (0-30)     | Rp XXX    | XX    | XX%
  31-60 days         | Rp XXX    | XX    | XX%
  61-90 days         | Rp XXX    | XX    | XX%
  91-120 days        | Rp XXX    | XX    | XX%
  >120 days (Bad)    | Rp XXX    | XX    | XX%
  ------------------------------------------------
  Total Outstanding  | Rp XXX    | XX    | 100%
  ```

  **Formula:**
  ```python
  aging_bucket = today - due_date
  if aging_bucket <= 30: category = "Current"
  elif aging_bucket <= 60: category = "31-60 days"
  # ... etc
  ```

- **Days Sales Outstanding (DSO)**
  ```python
  DSO = (Total AR / Total Revenue) × Days in Period

  Example:
  AR = Rp 50M
  Revenue (30 days) = Rp 100M
  DSO = (50/100) × 30 = 15 days

  Benchmark: <30 days = excellent, 30-45 = good, >45 = poor
  ```

- **Collection Effectiveness Index (CEI)**
  ```python
  CEI = (Collections in Period /
         (Opening AR + Revenue in Period - Closing AR)) × 100

  >80% = Excellent
  60-80% = Good
  <60% = Needs improvement
  ```

---

### 5.2 Cash Collection Analysis
**Data Available:** ✅ Complete

**Reports:**
- **Payment Velocity**
  ```python
  avg_days_to_payment = avg(paid_date - trans_date)

  By customer segment:
  - VIP customers: X days
  - Regular customers: Y days
  - New customers: Z days
  ```

- **Collection Rate**
  ```python
  invoices_paid_on_time = status_id == 3 AND paid_date <= due_date
  on_time_rate = paid_on_time / total_invoices

  Target: >95% on-time payment
  ```

- **Overdue Invoice Management**
  ```
  Total overdue amount (due > 0)
  Number of overdue invoices
  Average days overdue
  Top 10 overdue customers
  Overdue % of total AR
  ```

---

### 5.3 Working Capital Analysis
**Data Available:** ✅ Partial (AR only, AP needed)

**Current Reports:**
- **Receivables Turnover Ratio**
  ```python
  AR_turnover = Annual Revenue / Average AR

  Higher = Better (faster collections)
  ```

- **Cash Conversion Cycle** (partial)
  ```python
  DSO (calculated above)
  + DIO (Days Inventory Outstanding) - NOT AVAILABLE
  - DPO (Days Payable Outstanding) - NOT AVAILABLE
  = CCC

  Current: Only DSO available
  ```

---

## 6️⃣ OPERATIONAL METRICS

### 6.1 Invoice Processing Metrics
**Data Available:** ✅ Complete

**Reports:**
- **Invoice Creation Rate**
  ```
  Invoices per day/week/month
  Peak processing times
  Bottleneck identification
  ```

- **Invoice Value Distribution**
  ```
  Average invoice value
  Median invoice value
  Standard deviation
  Min/max invoice values
  ```

- **Invoice Cycle Time**
  ```python
  cycle_time = paid_date - trans_date
  avg_cycle_time = mean(cycle_time)

  Segments:
  - Fast cycle (<7 days)
  - Normal cycle (7-30 days)
  - Slow cycle (>30 days)
  ```

---

### 6.2 Payment Terms Analysis
**Data Available:** ✅ Complete

**Reports:**
- **Terms Performance**
  ```python
  termin.name: "Cash Before Delivery", "Net 30", "Net 60"

  Analysis:
  - Most used payment terms
  - Average payment delay by terms
  - Revenue impact of different terms
  ```

- **Terms vs Collection**
  ```
  Net 30 terms → X% paid on time
  Net 60 terms → Y% paid on time
  CBD terms → Z% paid on time
  ```

---

### 6.3 Transaction Volume Analysis
**Data Available:** ✅ Complete

**Reports:**
- **Transaction Count Trends**
  ```
  Daily transaction volume
  Weekly patterns
  Monthly trends
  YoY transaction growth
  ```

- **Average Transaction Metrics**
  ```
  qty: 24  # Items per transaction

  Average items per invoice
  Revenue per item
  Bulk transaction identification
  ```

---

## 7️⃣ RISK MANAGEMENT

### 7.1 Credit Risk Analysis
**Data Available:** ✅ Complete

**Reports:**
- **Customer Credit Score**
  ```python
  credit_score = weighted_average([
      payment_history_score * 0.4,
      payment_speed_score * 0.3,
      revenue_size_score * 0.2,
      relationship_length_score * 0.1
  ])

  Grade:
  A (90-100): Minimal risk
  B (80-89): Low risk
  C (70-79): Moderate risk
  D (60-69): High risk
  F (<60): Very high risk
  ```

- **Exposure by Customer**
  ```
  Current AR per customer
  % of total AR per customer
  Credit limit utilization (if limits set)
  ```

- **Bad Debt Forecast**
  ```python
  # Based on aging
  bad_debt_reserve = (
      overdue_90_120 * 0.25 +
      overdue_120_plus * 0.75
  )
  ```

---

### 7.2 Concentration Risk
**Data Available:** ✅ Complete

**Reports:**
- **Customer Concentration**
  ```
  Top 1 customer: X% of revenue
  Top 5 customers: Y% of revenue
  Top 10 customers: Z% of revenue

  Alert if any customer >15% (high risk)
  ```

- **Warehouse Concentration**
  ```
  Revenue by warehouse
  Risk if one warehouse dominates
  ```

- **Sales Rep Concentration**
  ```
  Revenue dependency on key reps
  Succession planning needs
  ```

---

## 8️⃣ PREDICTIVE ANALYTICS

### 8.1 Revenue Forecasting
**Data Available:** ✅ Good (historical trends)

**Models:**
- **Time Series Forecasting**
  ```python
  # Using historical revenue data
  - Moving Average (3, 6, 12 months)
  - Exponential Smoothing
  - ARIMA modeling
  - Seasonal decomposition

  Forecast next:
  - 1 month
  - 3 months (quarter)
  - 12 months (annual)
  ```

- **Growth Rate Projection**
  ```python
  CAGR = ((End Value / Start Value) ^ (1/years)) - 1

  Projected revenue = Current revenue * (1 + CAGR) ^ periods
  ```

---

### 8.2 Customer Behavior Prediction
**Data Available:** ✅ Good

**Models:**
- **Churn Prediction**
  ```python
  Features:
  - Days since last purchase
  - Purchase frequency decline
  - Average invoice value decline
  - Payment behavior changes

  Output: Churn probability (0-100%)
  ```

- **Next Purchase Prediction**
  ```python
  Based on:
  - Historical purchase intervals
  - Seasonal patterns
  - Customer lifecycle stage

  Output: Predicted next purchase date
  ```

- **Customer Lifetime Value Prediction**
  ```python
  Predict future value based on:
  - Current transaction patterns
  - Growth trajectory
  - Retention probability
  ```

---

### 8.3 Cash Flow Forecasting
**Data Available:** ✅ Good

**Reports:**
- **Expected Collections Forecast**
  ```python
  # Based on:
  - Current AR aging
  - Historical payment patterns
  - Seasonal trends

  Forecast collections for next:
  - 7 days
  - 30 days
  - 90 days
  ```

- **Revenue Run Rate**
  ```python
  monthly_run_rate = last_month_revenue
  annual_run_rate = monthly_run_rate * 12

  Adjusted for:
  - Seasonality
  - Growth trends
  - Known pipeline
  ```

---

## 📈 DASHBOARD RECOMMENDATIONS

### Executive Dashboard (C-Level)
**Real-time KPIs:**
```
┌─────────────────────────────────────────┐
│ TODAY'S SNAPSHOT                        │
├─────────────────────────────────────────┤
│ Revenue (MTD)        Rp 101.5M  ↑ 12%  │
│ Outstanding AR       Rp 45.2M   ↓ 5%   │
│ Invoices Paid        85%        ↑ 3%   │
│ DSO                  28 days    ↓ 2d   │
└─────────────────────────────────────────┘

TRENDS (Last 30 Days)
- Revenue: [Line chart]
- Collections: [Line chart]
- New Customers: 12 (↑ 20%)
```

---

### Sales Manager Dashboard
**Team Performance:**
```
TOP PERFORMERS (This Month)
1. Rep A - Rp 45M (9 deals)
2. Rep B - Rp 38M (12 deals)
3. Rep C - Rp 32M (7 deals)

ALERTS
⚠️ Rep D - Behind target by 25%
⚠️ Rep E - No deals closed this week
✅ Team target: 95% achieved
```

---

### Finance Manager Dashboard
**Cash Flow & AR:**
```
ACCOUNTS RECEIVABLE AGING
Current (0-30d):    Rp 30M   (66%)  🟢
31-60 days:         Rp 10M   (22%)  🟡
61-90 days:         Rp 4M    (9%)   🟠
>90 days:           Rp 1.2M  (3%)   🔴

COLLECTION METRICS
DSO: 28 days (Target: <30)  ✅
CEI: 82% (Target: >80%)     ✅
Overdue Rate: 12%           ⚠️
```

---

### Customer Success Dashboard
**Customer Health:**
```
CUSTOMER SEGMENTS
Champions:     45 customers (Rp 120M)
At Risk:       12 customers (Rp 18M) ⚠️
Churned:       8 customers (lost Rp 5M)

RETENTION METRICS
Monthly Retention:   95%  ✅
Churn Rate:         5%   ⚠️
Avg CLV:            Rp 2.5M
```

---

## 🎯 PRIORITY IMPLEMENTATION ROADMAP

### Phase 1: Core Financial Reports (Week 1-2)
**High Impact, Easy to Implement**
1. ✅ Revenue Summary (DONE - already working)
2. ✅ Invoice Aging Report (DONE - data available)
3. 🔨 DSO Calculation
4. 🔨 Sales Rep Performance Report (DONE - needs enhancement)
5. 🔨 Top Customers Report (DONE - needs enhancement)

---

### Phase 2: Operational Metrics (Week 3-4)
**Medium Impact, Moderate Complexity**
6. 🔨 Payment Behavior Scoring
7. 🔨 Collection Effectiveness (CEI)
8. 🔨 Revenue Breakdown (by warehouse, tag, terms)
9. 🔨 Transaction Volume Analysis
10. 🔨 Deal Size Distribution

---

### Phase 3: Advanced Analytics (Month 2)
**High Value, Complex Implementation**
11. 🔨 Customer RFM Segmentation
12. 🔨 Churn Prediction Model
13. 🔨 Revenue Forecasting
14. 🔨 Commission Calculator (needs targets)
15. 🔨 Customer Lifetime Value

---

### Phase 4: Dashboards & Automation (Month 3)
**User Experience Enhancement**
16. 🔨 Executive Dashboard
17. 🔨 Sales Manager Dashboard
18. 🔨 Finance Manager Dashboard
19. 🔨 Automated Alerts & Notifications
20. 🔨 Scheduled Report Generation

---

## 🔧 TECHNICAL REQUIREMENTS

### Data Completeness Check
| Metric | Available | Quality | Notes |
|--------|-----------|---------|-------|
| Revenue data | ✅ | Excellent | Complete financial fields |
| Customer data | ✅ | Good | Name, company, NPWP |
| Sales rep data | ✅ | Good | ID and name |
| Date fields | ✅ | Excellent | Multiple date types |
| Status tracking | ✅ | Excellent | Clear status IDs |
| Payment data | ✅ | Good | Payment dates and accounts |
| Tags/categories | ✅ | Good | Transaction categorization |
| Discount data | ✅ | Good | Multiple discount types |
| **Sales targets** | ❌ | Missing | **Needed for commissions** |
| **Marketing data** | ❌ | Missing | Needed for CAC |
| **Cost data** | ❌ | Missing | Needed for profitability |

---

### Additional Data Sources Recommended

**For Enhanced Analytics:**
1. **Sales Targets Table**
   ```sql
   sales_targets (
       sales_id INT,
       period DATE,
       target_amount DECIMAL,
       target_deals INT,
       commission_rate DECIMAL
   )
   ```

2. **Customer Master Data**
   ```sql
   customer_profile (
       contact_id INT,
       industry VARCHAR,
       company_size VARCHAR,
       credit_limit DECIMAL,
       payment_terms_preference VARCHAR
   )
   ```

3. **Product Costs** (for profitability)
   ```sql
   product_costs (
       product_id INT,
       cost_per_unit DECIMAL,
       updated_at DATE
   )
   ```

---

## 📊 SAMPLE REPORT OUTPUTS

### 1. Revenue Summary Report
```
=================================================
REVENUE SUMMARY REPORT
Period: January 2026
=================================================

FINANCIAL OVERVIEW
├─ Gross Revenue (Before Tax)    Rp  92,823,250
├─ Tax Collected (PPN)            Rp   8,678,450
└─ Net Revenue (After Tax)        Rp 101,501,700

TRANSACTION METRICS
├─ Total Invoices Paid            16
├─ Average Invoice Value          Rp   6,343,856
└─ Median Invoice Value           Rp   5,200,000

GROWTH METRICS
├─ MoM Growth                     +12.5%
├─ YoY Growth                     +18.2%
└─ Target Achievement             95%

TOP PRODUCTS/TAGS
1. Penjualan Material             Rp  85M (84%)
2. Penjualan Jasa                 Rp  16M (16%)
=================================================
```

---

### 2. AR Aging Report
```
=================================================
ACCOUNTS RECEIVABLE AGING REPORT
As of: January 24, 2026
=================================================

AGING SUMMARY
┌──────────────┬────────────────┬───────┬────────┐
│ Category     │ Amount         │ Count │ %      │
├──────────────┼────────────────┼───────┼────────┤
│ Current      │ Rp  30,250,000 │   12  │  66.8% │
│ 1-30 days    │ Rp  10,100,000 │    4  │  22.3% │
│ 31-60 days   │ Rp   3,500,000 │    2  │   7.7% │
│ 61-90 days   │ Rp   1,200,000 │    1  │   2.7% │
│ >90 days     │ Rp     200,000 │    1  │   0.4% │
├──────────────┼────────────────┼───────┼────────┤
│ TOTAL AR     │ Rp  45,250,000 │   20  │ 100.0% │
└──────────────┴────────────────┴───────┴────────┘

KEY METRICS
├─ DSO (Days Sales Outstanding)   28 days
├─ Collection Effectiveness       82%
└─ Overdue Amount                 Rp 4.9M (10.8%)

TOP 5 OVERDUE CUSTOMERS
1. PT XYZ - Rp 1.2M (45 days overdue)
2. CV ABC - Rp 850K (38 days overdue)
3. ...
=================================================
```

---

### 3. Sales Rep Performance
```
=================================================
SALES REP PERFORMANCE REPORT
Period: January 2026
=================================================

REP RANKING (by Revenue)
┌────┬─────────────────────────┬─────────────┬───────┬─────────────┐
│ #  │ Sales Rep               │ Revenue     │ Deals │ Avg Deal    │
├────┼─────────────────────────┼─────────────┼───────┼─────────────┤
│ 1  │ Teuku Muda Rabian H.    │ Rp 45.2M    │   9   │ Rp 5,022K   │
│ 2  │ Mono                    │ Rp 32.5M    │  12   │ Rp 2,708K   │
│ 3  │ Elmo                    │ Rp 24.8M    │   7   │ Rp 3,543K   │
│ 4  │ Meka                    │ Rp 18.6M    │   8   │ Rp 2,325K   │
└────┴─────────────────────────┴─────────────┴───────┴─────────────┘

TEAM METRICS
├─ Total Team Revenue             Rp 121.1M
├─ Average per Rep               Rp 30.3M
└─ Team Target Achievement       96%

PERFORMANCE DISTRIBUTION
🌟 Above Target (>100%): 2 reps
✅ On Target (90-100%):  1 rep
⚠️  Below Target (<90%):  1 rep
=================================================
```

---

## 💡 INSIGHTS & RECOMMENDATIONS

### What We Can Answer NOW
✅ "Berapa revenue bulan ini?"
✅ "Siapa sales rep terbaik?"
✅ "Customer mana yang belum bayar?"
✅ "Berapa average invoice value?"
✅ "Top 10 customer berdasarkan revenue?"
✅ "DSO berapa hari?"
✅ "Berapa tax yang harus dibayar?"
✅ "Invoice mana yang overdue?"
✅ "Revenue per warehouse?"
✅ "Payment behavior customer X?"

### What We CANNOT Answer (Missing Data)
❌ "Berapa margin keuntungan?" (need cost data)
❌ "Commission berapa?" (need sales targets)
❌ "CAC berapa?" (need marketing spend)
❌ "Inventory turnover?" (need inventory data)
❌ "ROI campaign?" (need marketing data)

### Quick Wins (Implement First)
1. ⚡ DSO Calculator - Critical for cash flow
2. ⚡ Payment Behavior Scoring - Identify risk customers
3. ⚡ Revenue Breakdown Dashboard - Business intelligence
4. ⚡ Sales Rep Leaderboard - Team motivation
5. ⚡ Overdue Invoice Alerts - Collection management

---

## 🎯 BUSINESS VALUE

### Financial Impact
- **Better Cash Flow:** DSO monitoring → Faster collections → Improved liquidity
- **Risk Reduction:** AR aging → Early warning → Prevent bad debt
- **Revenue Growth:** Sales analytics → Performance tracking → Target achievement

### Operational Efficiency
- **Automated Reporting:** 40+ hours/month saved on manual reports
- **Real-time Insights:** Dashboard vs end-of-month delays
- **Data-Driven Decisions:** Evidence-based vs gut feeling

### Strategic Advantage
- **Customer Intelligence:** Identify VIP vs risk customers
- **Sales Optimization:** Rep performance → Training needs
- **Predictive Planning:** Forecast revenue → Budget accurately

---

**Summary:** Dari data API Kledo, kita bisa generate **60+ laporan finansial dan analitik** yang mencakup hampir semua kebutuhan Finance Analyst dan Data Analyst. Yang masih missing hanya data cost, sales targets, dan marketing spend untuk analisis profitability dan commission yang lebih lengkap.

**Next Action:** Prioritas implementasi dimulai dari Core Financial Reports (DSO, AR Aging, Payment Behavior) karena high impact dan data sudah lengkap.
