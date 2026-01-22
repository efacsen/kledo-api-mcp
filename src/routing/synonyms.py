"""
Bilingual synonym dictionary for smart routing.

Maps alternate terms (English and Indonesian) to canonical forms,
and canonical terms to relevant tools.
"""

# Synonym map: alternate term -> canonical term
# English and Indonesian terms map to the same canonical form
SYNONYM_MAP: dict[str, str] = {
    # Sales/Revenue terms
    "revenue": "sales",
    "income": "sales",
    "pendapatan": "sales",
    "penjualan": "sales",
    "omzet": "sales",

    # Invoice terms
    "bill": "invoice",
    "bills": "invoice",
    "faktur": "invoice",
    "tagihan": "invoice",
    "nota": "invoice",

    # Customer terms
    "client": "customer",
    "clients": "customer",
    "pelanggan": "customer",
    "pembeli": "customer",
    "konsumen": "customer",

    # Vendor/Supplier terms
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
    "saldo": "balance",
    "kas": "cash",
    "uang": "cash",

    # Product terms
    "item": "product",
    "items": "product",
    "produk": "product",
    "barang": "product",

    # Order terms
    "orders": "order",
    "pesanan": "order",

    # Delivery terms
    "shipment": "delivery",
    "pengiriman": "delivery",
    "kirim": "delivery",

    # Stock/Inventory terms
    "inventory": "stock",
    "persediaan": "stock",
    "stok": "stock",
}


# Canonical term -> relevant tools mapping
TERM_TO_TOOLS: dict[str, list[str]] = {
    "sales": [
        "financial_sales_summary",
        "invoice_list_sales",
        "order_list_sales",
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
    ],
    "payable": [
        "invoice_list_purchase",
        "financial_purchase_summary",
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
