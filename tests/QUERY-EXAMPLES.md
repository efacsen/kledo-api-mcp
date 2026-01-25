# MCP Query Examples - Finance Analytics Tools

## Overview
You can now query the MCP server with 3 new finance analytics tools.

---

## Tool 1: Daily Revenue Breakdown

**Purpose**: See daily revenue trends for a time period

### Query 1: Last Month's Daily Revenue
```json
{
  "tool": "revenue_daily_breakdown",
  "arguments": {
    "date_from": "last_month"
  }
}
```

**Expected Answer**:
- Table showing daily net sales, tax, gross sales, running totals
- Daily statistics and averages
- Day-by-day breakdown for trend analysis

### Query 2: This Month's Daily Revenue
```json
{
  "tool": "revenue_daily_breakdown",
  "arguments": {
    "date_from": "this_month"
  }
}
```

### Query 3: Custom Date Range
```json
{
  "tool": "revenue_daily_breakdown",
  "arguments": {
    "date_from": "2026-01-01",
    "date_to": "2026-01-31"
  }
}
```

### Query 4: Last 7 Days
```json
{
  "tool": "revenue_daily_breakdown",
  "arguments": {
    "date_from": "last_7_days"
  }
}
```

---

## Tool 2: Outstanding Aging Report

**Purpose**: See unpaid/partially paid invoices grouped by age (collections priority)

### Query 1: All Outstanding Invoices (All Ages)
```json
{
  "tool": "outstanding_aging_report",
  "arguments": {}
}
```

**Expected Answer**:
- Invoices grouped by age: 0-30, 30-60, 60-90, 90+ days
- DSO (Days Sales Outstanding) metric
- Collections priority list for 90+ day overdue

### Query 2: Only Show Overdue (90+ Days Old)
```json
{
  "tool": "outstanding_aging_report",
  "arguments": {
    "min_days": 90
  }
}
```

**Expected Answer**:
- Only invoices 90+ days old
- Sorted by age (oldest first)
- Perfect for collections team focus

### Query 3: Show Aging (30+ Days)
```json
{
  "tool": "outstanding_aging_report",
  "arguments": {
    "min_days": 30
  }
}
```

---

## Tool 3: Customer Concentration Report

**Purpose**: Analyze business risk through 80/20 Pareto analysis

### Query 1: This Month's Concentration
```json
{
  "tool": "customer_concentration_report",
  "arguments": {
    "date_from": "this_month"
  }
}
```

**Expected Answer**:
- Risk level: 🟢 GREEN, 🟡 AMBER, or 🔴 RED
- Top 5 customers: X% of revenue
- Pareto analysis: How many customers = 80% revenue?
- Business interpretation and recommendations

### Query 2: Last Month's Concentration
```json
{
  "tool": "customer_concentration_report",
  "arguments": {
    "date_from": "last_month"
  }
}
```

### Query 3: Year-to-Date Concentration
```json
{
  "tool": "customer_concentration_report",
  "arguments": {
    "date_from": "this_year"
  }
}
```

### Query 4: Custom Period Analysis
```json
{
  "tool": "customer_concentration_report",
  "arguments": {
    "date_from": "2026-01-01",
    "date_to": "2026-01-31"
  }
}
```

---

## Real-World Use Cases

### Daily Sales Meeting
**Question**: "What was yesterday's revenue?"

```json
{
  "tool": "revenue_daily_breakdown",
  "arguments": {
    "date_from": "2026-01-23"
  }
}
```

### Collections Call
**Question**: "Who needs to be contacted today?"

```json
{
  "tool": "outstanding_aging_report",
  "arguments": {
    "min_days": 90
  }
}
```

### Board Meeting
**Question**: "What's our customer concentration risk?"

```json
{
  "tool": "customer_concentration_report",
  "arguments": {
    "date_from": "last_month"
  }
}
```

### Cash Flow Planning
**Question**: "What's our average days to payment?"

```json
{
  "tool": "outstanding_aging_report",
  "arguments": {}
}
```
*Look for DSO metric in the response*

### Strategic Planning
**Question**: "Should we focus on diversifying customers?"

```json
{
  "tool": "customer_concentration_report",
  "arguments": {
    "date_from": "this_year"
  }
}
```

---

## Supported Date Shortcuts

These work with `date_from` and `date_to` parameters:

- `"this_month"` - Current month (Jan 1 - Jan 31)
- `"last_month"` - Previous month
- `"this_year"` - Current year (Jan 1 - Dec 31)
- `"last_year"` - Previous year
- `"last_7_days"` - Last 7 calendar days
- `"last_30_days"` - Last 30 calendar days
- `"YYYY-MM-DD"` - Specific date

---

## Output Formats

All tools return markdown-formatted tables for easy reading:

**Daily Revenue Breakdown Output**:
```
# Daily Revenue Breakdown (PAID INVOICES ONLY)
**Period**: 2026-01-01 to 2026-01-31

## Daily Summary
| Date       | Invoices | Net Sales | Tax    | Gross Sales | Running Total |
|------------|----------|-----------|--------|-------------|----------------|
| 2026-01-19 | 1        | Rp 4.41M  | Rp 0   | Rp 4.41M    | Rp 4.41M      |
```

**Outstanding Aging Output**:
```
# Outstanding Aging Report (Piutang - Aging Analysis)
**Report Date**: 2026-01-24
**Total Outstanding**: Rp 50.5M
**Days Sales Outstanding (DSO)**: 35 days

## 🔴 CRITICAL - Way Overdue (90+ days)
**Count**: 2 invoices
**Total Outstanding**: Rp 25.0M
```

**Concentration Report Output**:
```
# Customer Concentration Report (Pareto 80/20 Analysis)
**Total Customers**: 10

## Risk Assessment
**Risk Level**: 🟡 AMBER - Moderate Concentration
**Top 5 Customers**: 52.3% of revenue
```

---

## Error Handling

If a query fails, you'll get a descriptive error message:

```
Error fetching daily revenue breakdown: No paid invoices found for period: 2026-02-01 to 2026-02-28
```

Common scenarios:
- Empty date ranges (no invoices)
- Invalid date formats
- API connection issues
- Missing authentication

---

## Next Steps

1. **Try a query**: Pick one of the examples above
2. **Check the results**: Validate the output makes business sense
3. **Use in your workflow**: Integrate into daily/weekly processes
4. **Provide feedback**: Let us know if the tools meet your needs

---

## Questions?

Check the implementation documentation:
- `/tests/IMPLEMENTATION-SUMMARY.md` - Technical details
- `/tests/05-UAT-EXECUTIVE-SUMMARY.md` - Overview and benefits
- `/tests/05-UAT-FINANCE-ANALYST-REPORT.md` - Detailed analysis

