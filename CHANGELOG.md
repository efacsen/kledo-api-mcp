# Changelog

### [FIX] Use server-side status_id filter for outstanding queries (09:33 UTC)
- outstanding_by_customer/vendor now use Kledo API status_id param instead of fetching all invoices
- ~8-18x fewer invoices fetched per query (38 instead of 701 AR, 127 instead of 987 AP)
- Verified: totals match exactly with Kledo UI
