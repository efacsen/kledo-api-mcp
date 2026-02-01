"""
Pattern library for idiomatic expressions in smart routing.

Maps common business phrases (English and Indonesian) to specific tools
with suggested parameters.
"""

from typing import Any


# Pattern library for compound expressions
# Each pattern has:
#   - patterns: list of phrase variations (English + Indonesian)
#   - tool: primary recommended tool
#   - params: dict of suggested parameters (or "auto_date_*" for date hints)
#   - alternative: optional secondary tool
#   - confidence: "definitive" or "context-dependent"
PATTERNS: list[dict[str, Any]] = [
    {
        "patterns": [
            "outstanding invoices",
            "unpaid invoices",
            "faktur belum lunas",
            "faktur belum dibayar",
        ],
        "tool": "invoice_list_sales",
        "params": {"status_id": 2},
        "confidence": "definitive",
    },
    {
        "patterns": [
            "who owes me money",
            "siapa yang hutang ke kita",
            "piutang belum dibayar",
            "accounts receivable",
        ],
        "tool": "invoice_get_totals",
        "params": {},
        "alternative": "invoice_list_sales",
        "confidence": "context-dependent",
    },
    {
        "patterns": [
            "this month's revenue",
            "pendapatan bulan ini",
            "this month's sales",
            "penjualan bulan ini",
        ],
        "tool": "financial_sales_summary",
        "params": "auto_date_this_month",
        "confidence": "definitive",
    },
    {
        "patterns": [
            "customers who haven't paid",
            "pelanggan yang belum bayar",
            "unpaid customers",
        ],
        "tool": "invoice_list_sales",
        "params": {"status_id": 2},
        "confidence": "definitive",
    },
    {
        "patterns": [
            "top customers",
            "pelanggan terbesar",
            "best customers",
            "customer ranking",
        ],
        "tool": "financial_sales_summary",
        "params": {},
        "confidence": "definitive",
    },
    {
        "patterns": [
            "sales per person",
            "sales by person",
            "sales per orang",
            "penjualan per orang",
            "penjualan per sales",
            "sales person performance",
            "performa sales",
            "ranking sales",
            "sales ranking",
            "top sales",
            "top performer",
            "siapa yang paling banyak jual",
            "sales bulan ini per orang",
            "era mono budi",
            "meka sales",
            "elmo sales",
            "rabian sales",
        ],
        "tool": "financial_sales_by_person",
        "params": "auto_date_this_month",
        "confidence": "definitive",
    },
    {
        "patterns": [
            "pending deliveries",
            "pengiriman tertunda",
            "unshipped orders",
            "what needs to ship",
        ],
        "tool": "delivery_get_pending",
        "params": {},
        "confidence": "definitive",
    },
    {
        "patterns": [
            "cash on hand",
            "saldo kas",
            "bank balances",
            "how much money do we have",
        ],
        "tool": "financial_bank_balances",
        "params": {},
        "confidence": "definitive",
    },
    {
        "patterns": [
            "vendor spending",
            "pengeluaran ke vendor",
            "supplier costs",
            "what did we spend",
        ],
        "tool": "financial_purchase_summary",
        "params": {},
        "confidence": "definitive",
    },
    {
        "patterns": [
            "customer history",
            "riwayat pelanggan",
            "transaction history",
            "what did customer buy",
        ],
        "tool": "contact_get_transactions",
        "params": {},
        "confidence": "context-dependent",
    },
    {
        "patterns": [
            "overdue invoices",
            "faktur jatuh tempo",
            "late payments",
        ],
        "tool": "invoice_get_totals",
        "params": {},
        "alternative": "invoice_list_sales",
        "confidence": "definitive",
    },
]


def match_pattern(query: str) -> dict[str, Any] | None:
    """
    Match a query against the idiomatic pattern library.

    Args:
        query: Natural language query string

    Returns:
        The matching pattern dict if found, None otherwise.
        Returns the first matching pattern.
    """
    query_lower = query.lower()

    for pattern in PATTERNS:
        for phrase in pattern["patterns"]:
            if phrase in query_lower:
                return pattern

    return None
