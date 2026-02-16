# Changelog

### [DOCS] Genericize README for public release (10:12 UTC)
- Removed business-specific commission calculation sections
- Removed specific revenue examples with currency amounts
- Genericized "For AI Models" section to be platform-agnostic
- Removed reference to specific record counts from internal deployments
- Removed deep-dive revenue formula details (internal business logic)
- Kept Quick Start, all 28 tools, configuration, deployment, troubleshooting
- Professional open-source tone focused on what the MCP server does, not business operations

### [DOCS] Sanitize test data (09:39 UTC)
- Replaced all real business data in `test_results_21_queries.json` with generic samples
- Replaced vendor/customer/sales rep names with generic placeholders
- Replaced real invoice numbers and financial amounts with dummy data
- Updated `CLAUDE.md` to remove company name

### [FIX] Use server-side status_id filter for outstanding queries (09:33 UTC)
- outstanding_by_customer/vendor now use Kledo API status_id param instead of fetching all invoices
- ~8-18x fewer invoices fetched per query (38 instead of 701 AR, 127 instead of 987 AP)
- Verified: totals match exactly with Kledo UI
