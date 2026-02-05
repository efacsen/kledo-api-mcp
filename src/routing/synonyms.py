"""
Bilingual synonym dictionary for smart routing.

Maps alternate terms (English and Indonesian) to canonical forms,
and canonical terms to relevant tools.
"""

# Synonym map: alternate term -> canonical term
# English and Indonesian terms map to the same canonical form
# Canonical terms also map to themselves for fuzzy matching
SYNONYM_MAP: dict[str, str] = {
    # Canonical terms (self-mapping for fuzzy lookup)
    "sales": "sales",
    "invoice": "invoice",
    "customer": "customer",
    "vendor": "vendor",
    "receivable": "receivable",
    "payable": "payable",
    "balance": "balance",
    "cash": "cash",
    "product": "product",
    "order": "order",
    "delivery": "delivery",
    "stock": "stock",

    # Sales/Revenue terms
    "revenue": "sales",
    "income": "sales",
    "pendapatan": "sales",
    "penjualan": "sales",
    "omzet": "sales",

    # Invoice terms
    "invoices": "invoice",
    "bill": "invoice",
    "bills": "invoice",
    "faktur": "invoice",
    "tagihan": "invoice",
    "nota": "invoice",

    # Customer terms
    "customers": "customer",
    "client": "customer",
    "clients": "customer",
    "pelanggan": "customer",
    "pembeli": "customer",
    "konsumen": "customer",

    # Vendor/Supplier terms
    "vendors": "vendor",
    "supplier": "vendor",
    "suppliers": "vendor",
    "pemasok": "vendor",

    # Receivable terms
    "receivables": "receivable",
    "piutang": "receivable",

    # Payable terms
    "payables": "payable",
    "hutang": "payable",
    "utang": "payable",

    # Balance/Cash terms
    "balances": "balance",
    "saldo": "balance",
    "kas": "cash",
    "uang": "cash",

    # Product terms
    "products": "product",
    "item": "product",
    "items": "product",
    "produk": "product",
    "barang": "product",

    # Order terms
    "orders": "order",
    "pesanan": "order",

    # Delivery terms
    "deliveries": "delivery",
    "shipment": "delivery",
    "shipments": "delivery",
    "pengiriman": "delivery",
    "kirim": "delivery",

    # Stock/Inventory terms
    "inventory": "stock",
    "persediaan": "stock",
    "stok": "stock",

    # Sales Person terms
    "salesperson": "salesperson",
    "sales_person": "salesperson",
    "salesrep": "salesperson",
    "sales rep": "salesperson",
    "per person": "salesperson",
    "per orang": "salesperson",
    "per sales": "salesperson",
    "ranking sales": "salesperson",
    "performer": "performer",
    "top performer": "performer",
    "performa": "performer",

    # Outstanding/aggregation terms
    "outstanding": "outstanding",
    "overdue": "outstanding",
    "telat": "outstanding",
    "terlambat": "outstanding",
    "jatuh tempo": "outstanding",

    # Aggregation action terms
    "per": "aggregation",
    "grouped": "aggregation",
    "group by": "aggregation",
    "breakdown": "aggregation",
    "ringkasan per": "aggregation",
}


# Canonical term -> relevant tools mapping
TERM_TO_TOOLS: dict[str, list[str]] = {
    "sales": [
        "financial_sales_summary",
        "financial_sales_by_person",
        "invoice_list_sales",
        "order_list_sales",
    ],
    "salesperson": [
        "financial_sales_by_person",
    ],
    "performer": [
        "financial_sales_by_person",
    ],
    "invoice": [
        "invoice_list_sales",
        "invoice_list_purchase",
        "invoice_get_detail",
        "invoice_get_totals",
    ],
    "customer": [
        "contact_list",
        "contact_get_detail",
        "contact_get_transactions",
    ],
    "vendor": [
        "contact_list",
        "invoice_list_purchase",
        "financial_purchase_summary",
    ],
    "receivable": [
        "invoice_get_totals",
        "invoice_list_sales",
        "outstanding_by_customer",
    ],
    "payable": [
        "invoice_list_purchase",
        "financial_purchase_summary",
        "outstanding_by_vendor",
    ],
    "outstanding": [
        "outstanding_by_customer",
        "outstanding_by_vendor",
        "invoice_get_totals",
        "invoice_list_sales",
    ],
    "aggregation": [
        "outstanding_by_customer",
        "outstanding_by_vendor",
        "financial_sales_summary",
        "financial_purchase_summary",
        "financial_sales_by_person",
    ],
    "balance": [
        "financial_bank_balances",
    ],
    "cash": [
        "financial_bank_balances",
    ],
    "product": [
        "product_list",
        "product_get_detail",
        "product_search_by_sku",
    ],
    "order": [
        "order_list_sales",
        "order_list_purchase",
        "order_get_detail",
    ],
    "delivery": [
        "delivery_list",
        "delivery_get_detail",
        "delivery_get_pending",
    ],
    "stock": [
        "product_list",
        "product_get_detail",
    ],
}


def normalize_term(term: str) -> str:
    """
    Normalize a term to its canonical form.

    Args:
        term: The input term (can be English or Indonesian)

    Returns:
        The canonical term if found in SYNONYM_MAP,
        otherwise the original term in lowercase
    """
    lower_term = term.lower()
    return SYNONYM_MAP.get(lower_term, lower_term)
