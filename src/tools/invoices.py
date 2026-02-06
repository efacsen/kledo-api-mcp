"""
Invoice tools for Kledo MCP Server
"""
import re
from collections import defaultdict
from datetime import timedelta
from typing import Any, Dict
from mcp.types import Tool
from rapidfuzz import fuzz

from ..kledo_client import KledoAPIClient
from ..utils.helpers import (
    parse_date_range, format_currency, safe_get,
    parse_indonesian_date_phrase, get_jakarta_today,
    calculate_overdue_days, categorize_overdue_invoices
)


def format_customer_display(invoice: dict) -> str:
    """
    Format customer/vendor display name prioritizing company name.
    
    For B2B context, company name is more important than contact person name.
    
    Args:
        invoice: Invoice dictionary with contact data
    
    Returns:
        Formatted customer string
        
    Examples:
        - Company only: "PT Nippon Paint Indonesia"
        - Company + Contact: "PT Nippon Paint Indonesia (Darma)"
        - Contact only: "Suwito"
    """
    contact_name = (safe_get(invoice, "contact.name", "") or "").strip()
    company_name = (safe_get(invoice, "contact.company", "") or "").strip()
    
    # Priority 1: Company name with contact in parentheses (if different)
    if company_name:
        if contact_name and contact_name.lower() != company_name.lower():
            return f"{company_name} ({contact_name})"
        return company_name
    
    # Priority 2: Contact name only (fallback)
    if contact_name:
        return contact_name
    
    # Priority 3: Unknown
    return "Unknown"


def fuzzy_company_match(search_term: str, company_name: str, contact_name: str, threshold: int = 55) -> tuple[bool, float]:
    """
    Fuzzy match search term against company name and contact name.
    
    Args:
        search_term: Search input (e.g., "Nipsea", "Nipon")
        company_name: Company/organization name
        contact_name: Contact person name
        threshold: Minimum match score (0-100), default 70
    
    Returns:
        Tuple of (is_match, best_score)
        
    Examples:
        - "Nipsea" matches "PT Nippon Paint Indonesia" (fuzzy)
        - "Nipon" matches "PT Nippon Paint Indonesia" (fuzzy)
        - "Nippon" matches "PT Nippon Paint Indonesia" (exact substring)
    """
    search_lower = search_term.lower().strip()
    company_lower = (company_name or "").lower().strip()
    contact_lower = (contact_name or "").lower().strip()
    
    # Skip very short terms
    if len(search_lower) < 3:
        return False, 0.0
    
    best_score = 0.0
    
    # Check exact substring match first (highest priority)
    if search_lower in company_lower:
        best_score = 100.0
    elif search_lower in contact_lower:
        best_score = 90.0
    else:
        # Fuzzy matching - try multiple algorithms
        if company_lower:
            # partial_ratio: Good for substring matches
            partial_score = fuzz.partial_ratio(search_lower, company_lower)
            # token_sort_ratio: Good for word order variations
            token_score = fuzz.token_sort_ratio(search_lower, company_lower)
            company_score = max(partial_score, token_score)
            best_score = max(best_score, company_score)
        
        if contact_lower:
            partial_score = fuzz.partial_ratio(search_lower, contact_lower)
            token_score = fuzz.token_sort_ratio(search_lower, contact_lower)
            contact_score = max(partial_score, token_score) * 0.9  # Slightly lower priority
            best_score = max(best_score, contact_score)
    
    return best_score >= threshold, best_score


def filter_invoices_by_company_fuzzy(invoices: list[dict], search_term: str) -> list[dict]:
    """
    Filter invoices using fuzzy matching on company names and contact names.
    
    Args:
        invoices: List of invoice dictionaries
        search_term: Search term to match fuzzily
    
    Returns:
        Filtered list of invoices sorted by match quality
        
    Examples:
        - "Nipsea" → matches "PT Nippon Paint Indonesia"
        - "Nipon" → matches "PT Nippon Paint Indonesia"
        - "Kurnia" → matches "PT. KURNIA PROPERTINDO SEJAHTERA"
    """
    matches = []
    
    for invoice in invoices:
        company_name = safe_get(invoice, "contact.company", "")
        contact_name = safe_get(invoice, "contact.name", "")
        
        is_match, score = fuzzy_company_match(search_term, company_name, contact_name)
        
        if is_match:
            matches.append((invoice, score))
    
    # Sort by score (best matches first)
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return [inv for inv, score in matches]


def extract_invoice_digits(ref_number: str) -> list[str]:
    """
    Extract numeric sequences from invoice reference numbers.

    Examples:
    - "INV/26/JAN/01153" -> ["26", "01153"]
    - "INV-2024-001234" -> ["2024", "001234"]
    - "123" -> ["123"]
    """
    # Find all sequences of digits
    matches = re.findall(r'\d+', ref_number)
    return matches


def fuzzy_invoice_match(search_term: str, invoice_ref_number: str, threshold: int = 80) -> tuple[bool, float]:
    """
    Check if search term fuzzily matches any numeric part of invoice reference number.

    Args:
        search_term: The search input (e.g., "1153")
        invoice_ref_number: Invoice reference number (e.g., "INV/26/JAN/01153")
        threshold: Minimum match score (0-100), default 80

    Returns:
        Tuple of (is_match, score) where score is between 0-100
    """
    # Skip fuzzy matching for very short terms to avoid false positives
    if len(search_term) < 3:
        return False, 0.0

    # Skip if search term is all non-digits (probably customer name search)
    if not re.search(r'\d', search_term):
        return False, 0.0

    # Extract numeric parts from invoice number
    invoice_digits = extract_invoice_digits(invoice_ref_number)

    best_score = 0.0

    for invoice_digit in invoice_digits:
        # Try exact substring match first (highest score)
        if search_term in invoice_digit:
            substrate_ratio = len(search_term) / max(len(invoice_digit), 1)
            if substrate_ratio >= 0.3:  # At least 30% coverage for meaningful match
                best_score = max(best_score, 100 - (len(invoice_digit) - len(search_term)))

        # Try fuzzy matching
        score = fuzz.ratio(search_term, invoice_digit)
        best_score = max(best_score, score)

    return best_score >= threshold, best_score


def filter_invoices_by_fuzzy_search(invoices: list[dict], search_term: str) -> list[dict]:
    """
    Filter invoices using fuzzy matching on reference numbers.

    Args:
        invoices: List of invoice dictionaries
        search_term: Search term to match fuzzily

    Returns:
        Filtered list of invoices
    """
    matches = []

    for invoice in invoices:
        ref_number = safe_get(invoice, "ref_number", "").strip()
        if not ref_number:
            continue

        is_match, score = fuzzy_invoice_match(search_term, ref_number)
        if is_match:
            matches.append((invoice, score))

    # Sort by score (best matches first)
    matches.sort(key=lambda x: x[1], reverse=True)

    # Return just the invoices, sorted by match quality
    return [inv for inv, score in matches]


def should_use_fuzzy_search(search_term: str) -> bool:
    """
    Determine if fuzzy search should be used for a search term.

    Triggers fuzzy search when:
    - Search term is 3+ characters
    - Contains at least one digit
    - Not a typical name (no spaces, reasonable length)
    """
    if not search_term or len(search_term) < 3:
        return False

    # Must contain at least one digit
    if not re.search(r'\d', search_term):
        return False

    # Avoid triggering on complex search terms (with spaces, commas, etc.)
    if re.search(r'[,\s]', search_term):
        return False

    return True


def get_tools() -> list[Tool]:
    """Get list of invoice tools."""
    return [
        Tool(
            name="invoice_list_sales",
            description="""List sales invoices with optional filtering.

Shows invoice details including Net Sales (Penjualan Neto), Gross Sales (Penjualan Bruto), payment status, and customer info.

Displays company name prominently for B2B customers (e.g., 'PT Nippon Paint Indonesia (Darma)').

Supports due date filtering and overdue analysis with aging buckets.

Status codes (VERIFIED):
- 1 = Belum Dibayar (Unpaid)
- 2 = Dibayar Sebagian (Partially Paid)
- 3 = Lunas (Fully Paid) - Use this for revenue calculation""",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search invoice number, customer name, or company name. Supports fuzzy search for both invoice numbers (e.g., '1153' → 'INV/26/JAN/01153') and company names (e.g., 'Nipsea' → 'PT Nippon Paint Indonesia')"
                    },
                    "contact_id": {
                        "type": "integer",
                        "description": "Filter by customer ID"
                    },
                    "status_id": {
                        "type": "integer",
                        "description": "Filter by status: 1=Belum Dibayar (Unpaid), 2=Dibayar Sebagian (Partial), 3=Lunas (Paid)"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date for invoice date filter (YYYY-MM-DD or 'last_month', 'this_month', etc.)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date for invoice date filter (YYYY-MM-DD)"
                    },
                    "due_date_from": {
                        "type": "string",
                        "description": "Start date for due_date filter (YYYY-MM-DD or Indonesian phrase like 'minggu ini', 'bulan lalu'). Use for 'jatuh tempo' queries."
                    },
                    "due_date_to": {
                        "type": "string",
                        "description": "End date for due_date filter (YYYY-MM-DD or Indonesian phrase)"
                    },
                    "overdue_days": {
                        "type": "integer",
                        "description": "Filter invoices overdue by at least this many days. E.g., 30 for 'telat lebih dari 30 hari'. Use 0 for any overdue invoice."
                    },
                    "overdue_only": {
                        "type": "boolean",
                        "description": "If true, show only overdue invoices (due_date < today Jakarta time). Shortcut for overdue_days=0."
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 50, max: 100)"
                    },
                    "invoice_selection": {
                        "type": "string",
                        "description": "When fuzzy search returns multiple matches, use this to select invoice(s). Supports: single number ('1'), multiple ('1,2,3'), range ('1-5'), or 'all' for all matches, 'summary' for aggregate only."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="invoice_get_detail",
            description="Get detailed information about a specific invoice including line items.",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {
                        "type": "integer",
                        "description": "Invoice ID"
                    }
                },
                "required": ["invoice_id"]
            }
        ),
        Tool(
            name="invoice_get_totals",
            description="Get summary totals for sales invoices (total outstanding, paid, overdue, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Start date filter"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date filter"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="invoice_list_purchase",
            description="""List purchase invoices (bills from vendors) with optional filtering.

Displays vendor company name prominently for B2B vendors.

Supports filtering:
- Due date range (e.g., "purchase invoice yang jatuh tempo minggu ini")
- Overdue threshold (e.g., "purchase invoice yang telat lebih dari 30 hari")
- Vendor name with fuzzy matching (e.g., "purchase invoice dari vendor Nippon")
- Minimum outstanding amount per vendor (e.g., "vendor dengan outstanding diatas 10 juta")
- Aging buckets for overdue invoices (1-30, 31-60, 60+ days)

Status codes: 1=Belum Dibayar (Unpaid), 3=Lunas (Paid)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search term for vendor name or company name. Supports fuzzy matching (e.g., 'Nipsea' → 'PT Nippon Paint Indonesia')"
                    },
                    "vendor_name": {
                        "type": "string",
                        "description": "Filter by vendor name using fuzzy matching (e.g., 'Nippon', 'Nipsea'). Resolves to vendor contact_id automatically. If multiple vendors match, returns disambiguation list."
                    },
                    "contact_id": {
                        "type": "integer",
                        "description": "Filter by vendor ID"
                    },
                    "min_outstanding": {
                        "type": "number",
                        "description": "Minimum total outstanding amount per vendor. Only returns vendors with total outstanding >= this amount. Amount is in IDR (e.g., 10000000 for 10 juta). Applied AFTER vendor-level aggregation."
                    },
                    "status_id": {
                        "type": "integer",
                        "description": "Filter by status: 1=Belum Dibayar (Unpaid), 3=Lunas (Paid)"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date for invoice date filter (YYYY-MM-DD or 'last_month', 'this_month', etc.)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date for invoice date filter (YYYY-MM-DD)"
                    },
                    "due_date_from": {
                        "type": "string",
                        "description": "Start date for due_date filter (YYYY-MM-DD or Indonesian phrase like 'minggu ini', 'bulan lalu'). Use for 'jatuh tempo' queries."
                    },
                    "due_date_to": {
                        "type": "string",
                        "description": "End date for due_date filter (YYYY-MM-DD or Indonesian phrase)"
                    },
                    "overdue_days": {
                        "type": "integer",
                        "description": "Filter purchase invoices overdue by at least this many days. E.g., 30 for 'telat lebih dari 30 hari'. Use 0 for any overdue invoice."
                    },
                    "overdue_only": {
                        "type": "boolean",
                        "description": "If true, show only overdue purchase invoices (due_date < today Jakarta time). Shortcut for overdue_days=0."
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 50, max: 100)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="outstanding_by_customer",
            description="""Get outstanding amounts grouped by customer.

Shows which customers owe money, with totals per customer and individual invoice details.
Each invoice shows age in days overdue (e.g., "45 hari overdue") using Jakarta timezone.

Default sort: highest outstanding first. Capped at top 10 for readability.
Supports filtering by minimum outstanding amount and overdue threshold.

Contact type: Uses type_id=3 (Customer/pelanggan) from Kledo contacts.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_outstanding": {
                        "type": "number",
                        "description": "Minimum total outstanding per customer (IDR). Applied AFTER grouping (HAVING semantics). E.g., 10000000 for '>10 juta'."
                    },
                    "overdue_days": {
                        "type": "integer",
                        "description": "Only include invoices overdue by at least this many days. E.g., 30 for '>30 hari overdue'. Applied BEFORE grouping (WHERE semantics)."
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["amount", "count", "overdue"],
                        "description": "Sort results by: 'amount' (total outstanding, default), 'count' (invoice count), 'overdue' (max overdue days)"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date filter for invoice date (YYYY-MM-DD or 'last_month', 'this_month')"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date filter for invoice date (YYYY-MM-DD)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="outstanding_by_vendor",
            description="""Get outstanding amounts grouped by vendor (supplier).

Shows which vendors we owe money to, with totals per vendor and individual invoice details.
Each invoice shows age in days overdue using Jakarta timezone.

Default sort: highest outstanding first. Capped at top 10 for readability.
Supports filtering by minimum outstanding amount and overdue threshold.

Contact type: Uses type_id=1 (Vendor/pemasok) from Kledo contacts.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_outstanding": {
                        "type": "number",
                        "description": "Minimum total outstanding per vendor (IDR). Applied AFTER grouping (HAVING semantics). E.g., 5000000 for '>5 juta'."
                    },
                    "overdue_days": {
                        "type": "integer",
                        "description": "Only include invoices overdue by at least this many days. Applied BEFORE grouping (WHERE semantics)."
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["amount", "count", "overdue"],
                        "description": "Sort results by: 'amount' (total outstanding, default), 'count' (invoice count), 'overdue' (max overdue days)"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date filter for invoice date (YYYY-MM-DD or 'last_month', 'this_month')"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date filter for invoice date (YYYY-MM-DD)"
                    }
                },
                "required": []
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any], client: KledoAPIClient) -> str:
    """Handle invoice tool calls."""
    if name == "invoice_list_sales":
        return await _list_sales_invoices(arguments, client)
    elif name == "invoice_get_detail":
        return await _get_invoice_detail(arguments, client)
    elif name == "invoice_get_totals":
        return await _get_invoice_totals(arguments, client)
    elif name == "invoice_list_purchase":
        return await _list_purchase_invoices(arguments, client)
    elif name == "outstanding_by_customer":
        return await _outstanding_by_customer(arguments, client)
    elif name == "outstanding_by_vendor":
        return await _outstanding_by_vendor(arguments, client)
    else:
        return f"Unknown invoice tool: {name}"


async def _list_sales_invoices(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """List sales invoices."""
    # Parse date range (for invoice date)
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    # Parse due date range
    due_date_from = args.get("due_date_from")
    due_date_to = args.get("due_date_to")
    overdue_only = args.get("overdue_only", False)
    overdue_days = args.get("overdue_days")

    # Handle Indonesian date phrases for due_date
    if due_date_from:
        parsed_dates = parse_indonesian_date_phrase(due_date_from)
        if parsed_dates[0] is not None:
            due_date_from = parsed_dates[0].isoformat()
            if due_date_to is None and parsed_dates[1] is not None:
                due_date_to = parsed_dates[1].isoformat()

    if due_date_to and not due_date_from:
        parsed_dates = parse_indonesian_date_phrase(due_date_to)
        if parsed_dates[1] is not None:
            due_date_to = parsed_dates[1].isoformat()

    # Handle overdue filtering
    today_jakarta = get_jakarta_today()
    if overdue_only:
        # Set due_date_to to yesterday (invoices due before today are overdue)
        yesterday = today_jakarta - timedelta(days=1)
        due_date_to = yesterday.isoformat()

    if overdue_days is not None:
        # Calculate cutoff date: today - overdue_days
        cutoff_date = today_jakarta - timedelta(days=overdue_days)
        due_date_to = cutoff_date.isoformat()

    search_term = args.get("search", "").strip()
    fuzzy_search = should_use_fuzzy_search(search_term)
    invoice_selection = args.get("invoice_selection")

    # Track if we're in overdue mode for filtering and display
    is_overdue_mode = overdue_only or overdue_days is not None

    try:
        # For fuzzy search, try to get a broader set of invoices first
        if fuzzy_search:
            # Try fetching more invoices without the specific search term
            # Use larger page size and try without search initially
            data = await client.list_invoices(
                search="",  # No search filter initially
                contact_id=args.get("contact_id"),
                status_id=args.get("status_id"),
                date_from=date_from,
                date_to=date_to,
                due_date_from=due_date_from,
                due_date_to=due_date_to,
                per_page=200,  # Fetch more invoices for fuzzy matching
                force_refresh=args.get("force_refresh", False)
            )

            all_invoices = safe_get(data, "data.data", [])

            # Apply fuzzy filtering
            invoices = filter_invoices_by_fuzzy_search(all_invoices, search_term)

            # Apply client-side overdue filtering (exclude fully paid invoices)
            if is_overdue_mode and invoices:
                invoices = [inv for inv in invoices if float(safe_get(inv, "due", 0)) > 0 and safe_get(inv, "status_id") != 3]

            if not invoices:
                return f"No invoices found matching fuzzy search for '{search_term}'."

            # Handle invoice selection if specified
            if invoice_selection is not None:
                action_type, indices = parse_invoice_selection(str(invoice_selection), len(invoices))
                
                if action_type == "invalid":
                    return f"❌ Invalid selection '{invoice_selection}'. Pilih nomor 1-{len(invoices)}, atau 'all', atau 'summary'."
                
                elif action_type == "summary":
                    # Return aggregate summary only
                    total_net = sum(float(safe_get(inv, "subtotal", 0)) for inv in invoices)
                    total_tax = sum(float(safe_get(inv, "total_tax", 0)) for inv in invoices)
                    total_gross = sum(float(safe_get(inv, "amount_after_tax", 0)) for inv in invoices)
                    total_due = sum(float(safe_get(inv, "due", 0)) for inv in invoices)
                    total_paid = total_gross - total_due
                    
                    result = [f"# Summary: {len(invoices)} Invoices for '{search_term}'\n"]
                    result.append(f"**Penjualan Neto (Net Sales)**: {format_currency(total_net)}")
                    result.append(f"**PPN Collected**: {format_currency(total_tax)}")
                    result.append(f"**Penjualan Bruto (Gross Sales)**: {format_currency(total_gross)}")
                    result.append(f"**Paid**: {format_currency(total_paid)}")
                    result.append(f"**Outstanding**: {format_currency(total_due)}")
                    return "\n".join(result)
                
                elif action_type in ["single", "multiple", "all"]:
                    # Filter to selected invoices
                    invoices = [invoices[i] for i in indices]
                    # Continue to normal display below
                
            # If multiple matches and no selection, present disambiguation
            elif len(invoices) > 1:
                return _handle_fuzzy_search_disambiguation(invoices, search_term)

            # Single match or selected match - proceed with normal display
        else:
            # Normal search behavior
            data = await client.list_invoices(
                search=search_term,
                contact_id=args.get("contact_id"),
                status_id=args.get("status_id"),
                date_from=date_from,
                date_to=date_to,
                due_date_from=due_date_from,
                due_date_to=due_date_to,
                per_page=args.get("per_page", 50),
                force_refresh=args.get("force_refresh", False)
            )
            invoices = safe_get(data, "data.data", [])

            # Apply client-side overdue filtering (exclude fully paid invoices)
            if is_overdue_mode and invoices:
                invoices = [inv for inv in invoices if float(safe_get(inv, "due", 0)) > 0 and safe_get(inv, "status_id") != 3]

            # If no results and search_term looks like a company name, try client-side fuzzy search
            if not invoices and search_term and len(search_term) >= 3:
                # Fetch more invoices without search filter for client-side matching
                broader_data = await client.list_invoices(
                    search="",
                    contact_id=args.get("contact_id"),
                    status_id=args.get("status_id"),
                    date_from=date_from,
                    date_to=date_to,
                    due_date_from=due_date_from,
                    due_date_to=due_date_to,
                    per_page=100,
                    force_refresh=args.get("force_refresh", False)
                )
                all_invoices = safe_get(broader_data, "data.data", [])

                # Try fuzzy company name matching
                invoices = filter_invoices_by_company_fuzzy(all_invoices, search_term)

                # Apply client-side overdue filtering
                if is_overdue_mode and invoices:
                    invoices = [inv for inv in invoices if float(safe_get(inv, "due", 0)) > 0 and safe_get(inv, "status_id") != 3]
                
                if not invoices:
                    result = ["# Sales Invoices\n"]
                    result.append("No invoices found matching the criteria.")
                    return "\n".join(result)
            elif not invoices:
                result = ["# Sales Invoices\n"]
                result.append("No invoices found matching the criteria.")
                return "\n".join(result)
            
            # Handle invoice selection if specified (for normal search too)
            if invoice_selection is not None and len(invoices) > 0:
                action_type, indices = parse_invoice_selection(str(invoice_selection), len(invoices))
                
                if action_type == "invalid":
                    return f"❌ Invalid selection '{invoice_selection}'. Pilih nomor 1-{len(invoices)}, atau 'all', atau 'summary'."
                
                elif action_type == "summary":
                    # Return aggregate summary only
                    total_net = sum(float(safe_get(inv, "subtotal", 0)) for inv in invoices)
                    total_tax = sum(float(safe_get(inv, "total_tax", 0)) for inv in invoices)
                    total_gross = sum(float(safe_get(inv, "amount_after_tax", 0)) for inv in invoices)
                    total_due = sum(float(safe_get(inv, "due", 0)) for inv in invoices)
                    total_paid = total_gross - total_due
                    
                    result = [f"# Summary: {len(invoices)} Invoices for '{search_term}'\n"]
                    result.append(f"**Penjualan Neto (Net Sales)**: {format_currency(total_net)}")
                    result.append(f"**PPN Collected**: {format_currency(total_tax)}")
                    result.append(f"**Penjualan Bruto (Gross Sales)**: {format_currency(total_gross)}")
                    result.append(f"**Paid**: {format_currency(total_paid)}")
                    result.append(f"**Outstanding**: {format_currency(total_due)}")
                    return "\n".join(result)
                
                elif action_type in ["single", "multiple", "all"]:
                    # Filter to selected invoices
                    invoices = [invoices[i] for i in indices]
            
            # If multiple matches and no selection, present disambiguation
            elif len(invoices) > 1 and search_term:
                return _handle_fuzzy_search_disambiguation(invoices, search_term)

        result = ["# Sales Invoices\n"]

        result.append(f"**Total Found**: {len(invoices)}\n")

        # Calculate summary using clear business terminology
        total_net_sales = sum(float(safe_get(inv, "subtotal", 0)) for inv in invoices)
        total_tax = sum(float(safe_get(inv, "total_tax", 0)) for inv in invoices)
        total_gross_sales = sum(float(safe_get(inv, "amount_after_tax", 0)) for inv in invoices)
        total_due = sum(float(safe_get(inv, "due", 0)) for inv in invoices)
        total_paid = total_gross_sales - total_due

        result.append("## Summary:")
        result.append(f"**Penjualan Neto (Net Sales)**: {format_currency(total_net_sales)}")
        result.append(f"**PPN Collected**: {format_currency(total_tax)}")
        result.append(f"**Penjualan Bruto (Gross Sales)**: {format_currency(total_gross_sales)}")
        result.append(f"**Paid**: {format_currency(total_paid)}")
        result.append(f"**Outstanding**: {format_currency(total_due)}\n")

        # Add aging bucket display if in overdue mode
        if is_overdue_mode:
            buckets = categorize_overdue_invoices(invoices, today_jakarta)
            result.append("\n## Overdue Aging:\n")

            # Calculate totals for each bucket
            for bucket_name in ["1-30", "31-60", "60+"]:
                bucket_items = buckets[bucket_name]
                if bucket_items:
                    bucket_count = len(bucket_items)
                    bucket_outstanding = sum(float(safe_get(inv, "due", 0)) for inv, _ in bucket_items)
                    result.append(f"**{bucket_name} hari**: {bucket_count} invoices, {format_currency(bucket_outstanding)} outstanding")

            result.append("")  # Empty line

        result.append("\n## Invoices:\n")

        # Status mapping (VERIFIED from dashboard)
        status_map = {
            1: "Belum Dibayar (Unpaid)",
            2: "Dibayar Sebagian (Partially Paid)",
            3: "Lunas (Paid)"
        }

        for invoice in invoices[:20]:  # Limit display
            inv_number = safe_get(invoice, "ref_number", "N/A")
            customer = format_customer_display(invoice)  # Show company name + contact
            date = safe_get(invoice, "trans_date", "")
            due_date = safe_get(invoice, "due_date", "")

            # Get amounts
            subtotal = float(safe_get(invoice, "subtotal", 0))
            tax = float(safe_get(invoice, "total_tax", 0))
            amount_after_tax = float(safe_get(invoice, "amount_after_tax", 0))
            due = float(safe_get(invoice, "due", 0))

            status_id = safe_get(invoice, "status_id", 0)
            status = status_map.get(status_id, f"Status-{status_id}")

            result.append(f"### {inv_number}")
            result.append(f"- **Customer**: {customer}")
            result.append(f"- **Date**: {date}")
            if due_date:
                result.append(f"- **Due Date**: {due_date}")
                # Show overdue days if in overdue mode
                if is_overdue_mode:
                    overdue_days_count = calculate_overdue_days(due_date, today_jakarta)
                    if overdue_days_count > 0:
                        result.append(f"- **Overdue**: {overdue_days_count} hari")
            result.append(f"- **Net Sales**: {format_currency(subtotal)}")
            result.append(f"- **Tax (PPN)**: {format_currency(tax)}")
            result.append(f"- **Gross Sales**: {format_currency(amount_after_tax)}")
            result.append(f"- **Outstanding**: {format_currency(due)}")
            result.append(f"- **Status**: {status}\n")

        if len(invoices) > 20:
            result.append(f"... and {len(invoices) - 20} more invoices")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching sales invoices: {str(e)}"


def parse_invoice_selection(selection_str: str, max_count: int) -> tuple[str, list[int]]:
    """
    Parse invoice selection string into action type and indices.
    
    Args:
        selection_str: Selection string (e.g., "1", "1,2,3", "1-5", "all", "summary")
        max_count: Maximum number of invoices available
    
    Returns:
        Tuple of (action_type, selected_indices)
        - action_type: "single", "multiple", "all", "summary"
        - selected_indices: List of 0-based indices
    
    Examples:
        "1" → ("single", [0])
        "1,2,3" → ("multiple", [0, 1, 2])
        "1-5" → ("multiple", [0, 1, 2, 3, 4])
        "all" → ("all", [0, 1, ..., max_count-1])
        "summary" → ("summary", [])
    """
    selection_lower = selection_str.lower().strip()
    
    # Handle special keywords
    if selection_lower in ["all", "semua", "tampilkan semua", "show all"]:
        return "all", list(range(max_count))
    
    if selection_lower in ["summary", "total", "aggregate", "ringkasan"]:
        return "summary", []
    
    # Parse numeric selections
    indices = []
    
    # Handle ranges (e.g., "1-5")
    if '-' in selection_str and not selection_str.startswith('-'):
        try:
            parts = selection_str.split('-')
            if len(parts) == 2:
                start = int(parts[0].strip()) - 1  # Convert to 0-based
                end = int(parts[1].strip())  # End is inclusive, so don't subtract 1 yet
                indices = list(range(start, min(end, max_count)))
        except (ValueError, IndexError):
            pass
    
    # Handle comma-separated (e.g., "1,2,3" or "1, 2, 3")
    if not indices and ',' in selection_str:
        try:
            parts = selection_str.split(',')
            for part in parts:
                num = int(part.strip()) - 1  # Convert to 0-based
                if 0 <= num < max_count:
                    indices.append(num)
        except (ValueError, IndexError):
            pass
    
    # Handle single number
    if not indices:
        try:
            num = int(selection_str.strip()) - 1  # Convert to 0-based
            if 0 <= num < max_count:
                indices = [num]
        except (ValueError, IndexError):
            pass
    
    # Determine action type
    if not indices:
        return "invalid", []
    elif len(indices) == 1:
        return "single", indices
    else:
        return "multiple", indices


def _handle_fuzzy_search_disambiguation(invoices: list[dict], search_term: str) -> str:
    """
    Present multiple fuzzy search matches for user to choose from.

    Args:
        invoices: List of matching invoices (sorted by match quality)
        search_term: The original search term that triggered fuzzy search

    Returns:
        Formatted string showing numbered options and selection instructions
    """
    result = []
    
    result.append(f"Nemu {len(invoices)} invoice yang match dengan **'{search_term}'**\n")
    result.append("Pilih mana yang lo mau:\n")

    # Status mapping
    status_map = {
        1: "Belum Dibayar",
        2: "Dibayar Sebagian",
        3: "Lunas"
    }

    # Show up to 10 matches for clarity
    display_count = min(len(invoices), 10)
    
    for i, invoice in enumerate(invoices[:display_count], 1):
        inv_number = safe_get(invoice, "ref_number", "N/A")
        customer = format_customer_display(invoice)
        date = safe_get(invoice, "trans_date", "")
        amount = float(safe_get(invoice, "amount_after_tax", 0))
        due = float(safe_get(invoice, "due", 0))
        status_id = safe_get(invoice, "status_id", 0)
        status = status_map.get(status_id, f"Status-{status_id}")
        
        # Use emoji for status
        status_emoji = "✅" if status_id == 3 else "🔴" if due > 0 else "⚠️"

        result.append(f"**{i}. {inv_number}**")
        result.append(f"   {customer}")
        result.append(f"   {date} • {format_currency(amount)} {status_emoji} {status}")
        if i < display_count:  # Add separator except last item
            result.append("")

    if len(invoices) > display_count:
        result.append(f"\n... dan {len(invoices) - display_count} invoice lainnya\n")

    # Instructions - more conversational
    result.append("\n---")
    result.append("\n**Cara pilih:**")
    result.append("- **Satu invoice:** Bilang nomor nya (e.g., \"nomor 1\" atau \"yang pertama\")")
    result.append("- **Beberapa invoice:** Bilang nomor nya (e.g., \"nomor 1 dan 3\" atau \"1, 2, 5\")")
    result.append("- **Semua invoice:** Bilang \"semua\" atau \"tampilkan semua\"")
    result.append("- **Agregat/summary:** Bilang \"total\" atau \"summary\"\n")

    # Calculate aggregate for quick reference
    total_amount = sum(float(safe_get(inv, "amount_after_tax", 0)) for inv in invoices)
    total_outstanding = sum(float(safe_get(inv, "due", 0)) for inv in invoices)
    
    result.append("**Quick Summary:**")
    result.append(f"- Total {len(invoices)} invoices: {format_currency(total_amount)}")
    result.append(f"- Outstanding: {format_currency(total_outstanding)}")

    return "\n".join(result)


def _get_best_match_highlight(search_term: str, invoice_number: str) -> str:
    """
    Get a highlighted version showing the best matching part.

    Args:
        search_term: The search term
        invoice_number: The full invoice number

    Returns:
        String with the matching part highlighted (markdown code)
    """
    digits = extract_invoice_digits(invoice_number)

    # Find the best matching digit part
    best_match = None
    best_score = 0

    for digit_part in digits:
        if search_term in digit_part:
            # Exact substring match
            best_match = digit_part
            break
        else:
            # Check fuzzy match score
            score = fuzz.ratio(search_term, digit_part)
            if score > best_score and score >= 60:  # Lower threshold for highlighting
                best_score = score
                best_match = digit_part

    if best_match:
        highlighted = invoice_number.replace(best_match, f"**`{best_match}`**")
        return highlighted

    return invoice_number


async def _get_invoice_detail(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get invoice detail."""
    invoice_id = args.get("invoice_id")

    if not invoice_id:
        return "Error: invoice_id is required"

    try:
        data = await client.get_invoice_detail(invoice_id)

        invoice = safe_get(data, "data.data")
        if not invoice:
            return f"Invoice #{invoice_id} not found"

        result = ["# Invoice Details\n"]

        # Header info
        result.append(f"**Invoice Number**: {safe_get(invoice, 'trans_number', 'N/A')}")
        result.append(f"**Customer**: {safe_get(invoice, 'contact_name', 'Unknown')}")
        result.append(f"**Date**: {safe_get(invoice, 'trans_date', '')}")
        result.append(f"**Due Date**: {safe_get(invoice, 'due_date', '')}")
        result.append(f"**Status**: {safe_get(invoice, 'status_name', 'Unknown')}\n")

        # Amounts
        subtotal = safe_get(invoice, "subtotal", 0)
        tax = safe_get(invoice, "tax_amount", 0)
        total = safe_get(invoice, "grand_total", 0)
        paid = safe_get(invoice, "amount_paid", 0)
        due = total - paid

        result.append(f"**Subtotal**: {format_currency(subtotal)}")
        result.append(f"**Tax**: {format_currency(tax)}")
        result.append(f"**Total**: {format_currency(total)}")
        result.append(f"**Paid**: {format_currency(paid)}")
        result.append(f"**Due**: {format_currency(due)}\n")

        # Line items
        items = safe_get(invoice, "detail", [])
        if items:
            result.append("\n## Line Items:\n")
            for item in items:
                desc = safe_get(item, "desc", "Unknown item")
                qty = safe_get(item, "qty", 0)
                price = safe_get(item, "price", 0)
                amount = safe_get(item, "amount", 0)

                result.append(f"- **{desc}**")
                result.append(f"  - Qty: {qty} × {format_currency(price)} = {format_currency(amount)}")

        # Memo
        memo = safe_get(invoice, "memo")
        if memo:
            result.append(f"\n**Memo**: {memo}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching invoice details: {str(e)}"


async def _get_invoice_totals(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get invoice totals summary with smart fallback."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        # Try to get totals from the API endpoint
        data = await client.get(
            "invoices",
            "totals",
            params={
                "date_from": date_from,
                "date_to": date_to
            },
            cache_category="invoices"
        )

        result = ["# Invoice Totals Summary\n"]

        if date_from:
            result.append(f"**Period**: {date_from} to {date_to or 'present'}\n")

        totals = safe_get(data, "data", {})

        # Check if we got meaningful data from the totals endpoint
        total_amount = float(safe_get(totals, "amount_after_tax", 0))
        total_due = float(safe_get(totals, "due", 0))
        total_paid = float(safe_get(totals, "paid", 0))
        
        # Fallback: If totals are zero but date filtering was requested,
        # fetch the actual invoice list and calculate manually
        if total_amount == 0 and (date_from or date_to):
            result.append("_Note: Calculating totals from invoice list (API totals endpoint returned zero)_\n")
            
            # Fetch invoices with date filter
            invoices_data = await client.list_invoices(
                date_from=date_from,
                date_to=date_to,
                per_page=100,  # Get more results
                force_refresh=False
            )
            
            invoices = safe_get(invoices_data, "data.data", [])
            
            if invoices:
                # Calculate totals manually from invoice list
                total_amount = sum(float(safe_get(inv, "amount_after_tax", 0)) for inv in invoices)
                total_due = sum(float(safe_get(inv, "due", 0)) for inv in invoices)
                total_paid = total_amount - total_due
                total_count = len(invoices)
                
                # Count by status for better insight
                status_counts = {}
                for inv in invoices:
                    status_id = safe_get(inv, "status_id", 0)
                    status_counts[status_id] = status_counts.get(status_id, 0) + 1
                
                result.append(f"**Total Invoices**: {total_count}")
                result.append(f"**Total Amount**: {format_currency(total_amount)}")
                result.append(f"**Paid**: {format_currency(total_paid)}")
                result.append(f"**Outstanding**: {format_currency(total_due)}\n")
                
                # Add status breakdown
                result.append("## Status Breakdown:")
                status_names = {1: "Belum Dibayar (Unpaid)", 2: "Dibayar Sebagian (Partial)", 3: "Lunas (Paid)"}
                for status_id, count in sorted(status_counts.items()):
                    status_name = status_names.get(status_id, f"Status-{status_id}")
                    result.append(f"- **{status_name}**: {count} invoices")
                
                return "\n".join(result)
            else:
                result.append("No invoices found for the specified period.")
                return "\n".join(result)
        
        # Use API totals if available
        result.append(f"**Total Amount**: {format_currency(total_amount)}")
        result.append(f"**Paid**: {format_currency(total_paid)}")
        result.append(f"**Outstanding**: {format_currency(total_due)}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching invoice totals: {str(e)}"


async def _fetch_all_purchase_invoices(client: KledoAPIClient, date_from: str = None, date_to: str = None) -> list:
    """Fetch all purchase invoices for a date range (handles pagination)."""
    all_invoices = []
    page = 1
    max_pages = 20  # Safety limit

    while page <= max_pages:
        data = await client.get(
            "purchase_invoices",
            "list",
            params={
                "date_from": date_from,
                "date_to": date_to,
                "per_page": 100,
                "page": page
            },
            cache_category="invoices"
        )

        invoices = safe_get(data, "data.data", [])
        if not invoices:
            break

        all_invoices.extend(invoices)

        current_page = safe_get(data, "data.current_page", 1)
        last_page = safe_get(data, "data.last_page", 1)

        if current_page >= last_page:
            break
        page += 1

    return all_invoices


async def _outstanding_by_customer(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get outstanding amounts grouped by customer."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")
    min_outstanding = args.get("min_outstanding")
    overdue_days = args.get("overdue_days")
    sort_by = args.get("sort_by", "amount")

    # Parse date range
    if date_from and not date_to:
        from ..utils.helpers import parse_date_range
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        # Import _fetch_all_invoices from financial module pattern
        # Fetch all sales invoices
        all_invoices = []
        page = 1
        max_pages = 20

        while page <= max_pages:
            data = await client.get(
                "invoices",
                "list",
                params={
                    "date_from": date_from,
                    "date_to": date_to,
                    "per_page": 100,
                    "page": page
                },
                cache_category="invoices"
            )

            invoices = safe_get(data, "data.data", [])
            if not invoices:
                break

            all_invoices.extend(invoices)

            current_page = safe_get(data, "data.current_page", 1)
            last_page = safe_get(data, "data.last_page", 1)

            if current_page >= last_page:
                break
            page += 1

        # Filter out fully paid and zero-due invoices
        all_invoices = [inv for inv in all_invoices if float(safe_get(inv, "due", 0)) > 0 and safe_get(inv, "status_id") != 3]

        if not all_invoices:
            return "No outstanding invoices found."

        # Get Jakarta today for overdue calculation
        today_jakarta = get_jakarta_today()

        # Apply overdue_days filter (WHERE clause)
        if overdue_days is not None:
            filtered_invoices = []
            for inv in all_invoices:
                due_date_str = safe_get(inv, "due_date", "")
                if due_date_str:
                    days_overdue = calculate_overdue_days(due_date_str, today_jakarta)
                    if days_overdue >= overdue_days:
                        filtered_invoices.append(inv)
            all_invoices = filtered_invoices

        if not all_invoices:
            return f"No invoices found overdue by at least {overdue_days} days."

        # Group by customer
        customer_groups = defaultdict(lambda: {
            "total_outstanding": 0,
            "count": 0,
            "invoices": [],
            "max_overdue_days": 0
        })

        for inv in all_invoices:
            customer_name = format_customer_display(inv)
            due_amount = float(safe_get(inv, "due", 0))
            ref_number = safe_get(inv, "ref_number", "N/A")
            due_date_str = safe_get(inv, "due_date", "")

            # Calculate age
            age_days = calculate_overdue_days(due_date_str, today_jakarta) if due_date_str else 0

            # Accumulate
            customer_groups[customer_name]["total_outstanding"] += due_amount
            customer_groups[customer_name]["count"] += 1
            customer_groups[customer_name]["max_overdue_days"] = max(
                customer_groups[customer_name]["max_overdue_days"],
                age_days
            )

            # Store invoice details (limit to 5 per customer for memory efficiency)
            if len(customer_groups[customer_name]["invoices"]) < 5:
                customer_groups[customer_name]["invoices"].append({
                    "ref_number": ref_number,
                    "due": due_amount,
                    "age_days": age_days
                })

        # Apply min_outstanding filter (HAVING clause)
        if min_outstanding is not None:
            min_outstanding = float(min_outstanding)
            customer_groups = {
                name: data
                for name, data in customer_groups.items()
                if data["total_outstanding"] >= min_outstanding
            }

        if not customer_groups:
            return f"No customers with outstanding >= {format_currency(min_outstanding)}."

        # Sort results
        if sort_by == "count":
            sorted_customers = sorted(customer_groups.items(), key=lambda x: x[1]["count"], reverse=True)
        elif sort_by == "overdue":
            sorted_customers = sorted(customer_groups.items(), key=lambda x: x[1]["max_overdue_days"], reverse=True)
        else:  # Default: amount
            sorted_customers = sorted(customer_groups.items(), key=lambda x: x[1]["total_outstanding"], reverse=True)

        # Cap at top 10
        display_count = min(len(sorted_customers), 10)
        top_customers = sorted_customers[:display_count]
        overflow_customers = sorted_customers[display_count:]

        # Calculate totals
        grand_total = sum(data["total_outstanding"] for _, data in customer_groups.items())
        overflow_total = sum(data["total_outstanding"] for _, data in overflow_customers)

        # Format output
        result = ["# Outstanding by Customer\n"]
        result.append(f"**Total Customers with Outstanding**: {len(customer_groups)}")
        result.append(f"**Grand Total Outstanding**: {format_currency(grand_total)}\n")
        result.append("## Results:\n")

        for idx, (customer_name, data) in enumerate(top_customers, 1):
            result.append(f"{idx}. **{customer_name}**: {format_currency(data['total_outstanding'])} ({data['count']} invoices)")

            for inv in data["invoices"]:
                age_text = f"{inv['age_days']} hari overdue" if inv['age_days'] > 0 else "Not yet due"
                result.append(f"   - {inv['ref_number']} | {format_currency(inv['due'])} | {age_text}")

            remaining = data["count"] - len(data["invoices"])
            if remaining > 0:
                result.append(f"   ... dan {remaining} invoice lainnya\n")
            else:
                result.append("")

        if overflow_customers:
            result.append(f"... dan {len(overflow_customers)} customer lainnya dengan total {format_currency(overflow_total)}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching outstanding by customer: {str(e)}"


async def _outstanding_by_vendor(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """Get outstanding amounts grouped by vendor."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")
    min_outstanding = args.get("min_outstanding")
    overdue_days = args.get("overdue_days")
    sort_by = args.get("sort_by", "amount")

    # Parse date range
    if date_from and not date_to:
        from ..utils.helpers import parse_date_range
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    try:
        # Fetch all purchase invoices
        all_invoices = await _fetch_all_purchase_invoices(client, date_from, date_to)

        # Filter out fully paid and zero-due invoices
        all_invoices = [inv for inv in all_invoices if float(safe_get(inv, "due", 0)) > 0 and safe_get(inv, "status_id") != 3]

        if not all_invoices:
            return "No outstanding purchase invoices found."

        # Get Jakarta today for overdue calculation
        today_jakarta = get_jakarta_today()

        # Apply overdue_days filter (WHERE clause)
        if overdue_days is not None:
            filtered_invoices = []
            for inv in all_invoices:
                due_date_str = safe_get(inv, "due_date", "")
                if due_date_str:
                    days_overdue = calculate_overdue_days(due_date_str, today_jakarta)
                    if days_overdue >= overdue_days:
                        filtered_invoices.append(inv)
            all_invoices = filtered_invoices

        if not all_invoices:
            return f"No purchase invoices found overdue by at least {overdue_days} days."

        # Group by vendor
        vendor_groups = defaultdict(lambda: {
            "total_outstanding": 0,
            "count": 0,
            "invoices": [],
            "max_overdue_days": 0
        })

        for inv in all_invoices:
            vendor_name = format_customer_display(inv)  # Works for vendors too
            due_amount = float(safe_get(inv, "due", 0))
            ref_number = safe_get(inv, "ref_number", "N/A")
            due_date_str = safe_get(inv, "due_date", "")

            # Calculate age
            age_days = calculate_overdue_days(due_date_str, today_jakarta) if due_date_str else 0

            # Accumulate
            vendor_groups[vendor_name]["total_outstanding"] += due_amount
            vendor_groups[vendor_name]["count"] += 1
            vendor_groups[vendor_name]["max_overdue_days"] = max(
                vendor_groups[vendor_name]["max_overdue_days"],
                age_days
            )

            # Store invoice details (limit to 5 per vendor for memory efficiency)
            if len(vendor_groups[vendor_name]["invoices"]) < 5:
                vendor_groups[vendor_name]["invoices"].append({
                    "ref_number": ref_number,
                    "due": due_amount,
                    "age_days": age_days
                })

        # Apply min_outstanding filter (HAVING clause)
        if min_outstanding is not None:
            min_outstanding = float(min_outstanding)
            vendor_groups = {
                name: data
                for name, data in vendor_groups.items()
                if data["total_outstanding"] >= min_outstanding
            }

        if not vendor_groups:
            return f"No vendors with outstanding >= {format_currency(min_outstanding)}."

        # Sort results
        if sort_by == "count":
            sorted_vendors = sorted(vendor_groups.items(), key=lambda x: x[1]["count"], reverse=True)
        elif sort_by == "overdue":
            sorted_vendors = sorted(vendor_groups.items(), key=lambda x: x[1]["max_overdue_days"], reverse=True)
        else:  # Default: amount
            sorted_vendors = sorted(vendor_groups.items(), key=lambda x: x[1]["total_outstanding"], reverse=True)

        # Cap at top 10
        display_count = min(len(sorted_vendors), 10)
        top_vendors = sorted_vendors[:display_count]
        overflow_vendors = sorted_vendors[display_count:]

        # Calculate totals
        grand_total = sum(data["total_outstanding"] for _, data in vendor_groups.items())
        overflow_total = sum(data["total_outstanding"] for _, data in overflow_vendors)

        # Format output
        result = ["# Outstanding by Vendor\n"]
        result.append(f"**Total Vendors with Outstanding**: {len(vendor_groups)}")
        result.append(f"**Grand Total Outstanding**: {format_currency(grand_total)}\n")
        result.append("## Results:\n")

        for idx, (vendor_name, data) in enumerate(top_vendors, 1):
            result.append(f"{idx}. **{vendor_name}**: {format_currency(data['total_outstanding'])} ({data['count']} invoices)")

            for inv in data["invoices"]:
                age_text = f"{inv['age_days']} hari overdue" if inv['age_days'] > 0 else "Not yet due"
                result.append(f"   - {inv['ref_number']} | {format_currency(inv['due'])} | {age_text}")

            remaining = data["count"] - len(data["invoices"])
            if remaining > 0:
                result.append(f"   ... dan {remaining} invoice lainnya\n")
            else:
                result.append("")

        if overflow_vendors:
            result.append(f"... dan {len(overflow_vendors)} vendor lainnya dengan total {format_currency(overflow_total)}")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching outstanding by vendor: {str(e)}"


async def resolve_vendor_name(client: KledoAPIClient, vendor_name: str) -> int | list[dict] | None:
    """
    Resolve vendor name to contact_id via contacts API with fuzzy matching.

    Args:
        client: Kledo API client
        vendor_name: Vendor name to search (e.g., "Nippon", "Nipsea")

    Returns:
        - int: contact_id if single match found
        - list[dict]: list of matching contacts if multiple matches (for disambiguation)
        - None: if no matches found
    """
    if not vendor_name or len(vendor_name) < 3:
        return None

    try:
        # Step 1: Try API search with type_id=1 (vendors only)
        data = await client.list_contacts(search=vendor_name, type_id=1, per_page=100)
        contacts = safe_get(data, "data.data", [])

        if contacts:
            # API found results
            if len(contacts) == 1:
                # Single match - return contact_id directly
                return contacts[0]["id"]
            else:
                # Multiple results - apply fuzzy matching to rank
                matches = []
                for contact in contacts:
                    company_name = contact.get("company_name", "") or contact.get("company", "")
                    contact_name = contact.get("name", "")
                    is_match, score = fuzzy_company_match(vendor_name, company_name, contact_name)
                    if is_match:
                        matches.append((contact, score))

                if not matches:
                    # No fuzzy matches above threshold - return all API results for disambiguation
                    return contacts

                # Sort by score
                matches.sort(key=lambda x: x[1], reverse=True)

                # If single high-confidence match (>= 90), return that contact_id
                if len(matches) == 1 or (matches[0][1] >= 90 and matches[0][1] - matches[1][1] >= 10):
                    return matches[0][0]["id"]

                # Multiple good matches - return for disambiguation
                return [contact for contact, score in matches]

        # Step 2: API search returned no results - try broader fuzzy search
        # Fetch broader vendor list without search filter
        broader_data = await client.list_contacts(search="", type_id=1, per_page=200)
        all_vendors = safe_get(broader_data, "data.data", [])

        if not all_vendors:
            return None

        # Apply fuzzy matching to all vendors
        matches = []
        for contact in all_vendors:
            company_name = contact.get("company_name", "") or contact.get("company", "")
            contact_name = contact.get("name", "")
            is_match, score = fuzzy_company_match(vendor_name, company_name, contact_name, threshold=55)
            if is_match:
                matches.append((contact, score))

        if not matches:
            return None

        # Sort by score
        matches.sort(key=lambda x: x[1], reverse=True)

        if len(matches) == 1:
            # Single match - return contact_id
            return matches[0][0]["id"]
        else:
            # Multiple matches - return for disambiguation
            return [contact for contact, score in matches]

    except Exception as e:
        # Log error but don't fail - return None
        print(f"Error resolving vendor name '{vendor_name}': {e}")
        return None


async def _list_purchase_invoices(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """List purchase invoices."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")
    search_term = args.get("search", "").strip()

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    # Resolve vendor name to contact_id if provided
    vendor_name = args.get("vendor_name", "").strip()
    resolved_contact_id = args.get("contact_id")  # Existing param takes priority

    if vendor_name and not resolved_contact_id:
        resolution = await resolve_vendor_name(client, vendor_name)

        if resolution is None:
            return f"No vendors found matching '{vendor_name}'. Try a different name or check spelling."

        if isinstance(resolution, list):
            # Multiple matches - present disambiguation
            result = [f"Found {len(resolution)} vendors matching '{vendor_name}':\n"]
            for i, contact in enumerate(resolution, 1):
                name = contact.get("name", "Unknown")
                company = contact.get("company_name", "") or contact.get("company", "")
                display = f"{company} ({name})" if company and name != company else (company or name)
                result.append(f"**{i}.** {display} (ID: {contact['id']})")
            result.append(f"\nPlease specify which vendor by using contact_id parameter or a more specific vendor_name.")
            return "\n".join(result)

        # Single match - use resolved contact_id
        resolved_contact_id = resolution

    # Resolve due date filters
    due_date_from = args.get("due_date_from")
    due_date_to = args.get("due_date_to")

    if due_date_from:
        parsed_from, parsed_to = parse_indonesian_date_phrase(due_date_from)
        if parsed_from:
            due_date_from = parsed_from.isoformat()
            if not due_date_to:
                due_date_to = parsed_to.isoformat()

    if due_date_to and not isinstance(due_date_to, str):
        due_date_to = due_date_to.isoformat()
    elif due_date_to:
        parsed_from, parsed_to = parse_indonesian_date_phrase(due_date_to)
        if parsed_to:
            due_date_to = parsed_to.isoformat()

    # Handle overdue filtering
    overdue_only = args.get("overdue_only", False)
    overdue_days = args.get("overdue_days")
    is_overdue_query = overdue_only or overdue_days is not None

    if overdue_only and not due_date_to:
        today = get_jakarta_today()
        due_date_to = (today - timedelta(days=1)).isoformat()

    if overdue_days is not None and not due_date_to:
        today = get_jakarta_today()
        cutoff = today - timedelta(days=overdue_days)
        due_date_to = cutoff.isoformat()

    try:
        data = await client.get(
            "purchase_invoices",
            "list",
            params={
                "search": search_term,
                "contact_id": resolved_contact_id,
                "status_id": args.get("status_id"),
                "date_from": date_from,
                "date_to": date_to,
                "due_date_from": due_date_from,
                "due_date_to": due_date_to,
                "per_page": args.get("per_page", 50)
            },
            cache_category="invoices"
        )

        result = ["# Purchase Invoices\n"]

        invoices = safe_get(data, "data.data", [])

        # Apply client-side overdue filtering (exclude fully paid invoices)
        if is_overdue_query and invoices:
            invoices = [inv for inv in invoices if float(safe_get(inv, "due", 0)) > 0 and safe_get(inv, "status_id") != 3]

        # Apply minimum outstanding filter
        min_outstanding = args.get("min_outstanding")
        if min_outstanding is not None:
            min_outstanding = float(min_outstanding)
            # FILT-07: min_outstanding applies to total per VENDOR, not per invoice
            # Since we already filtered by contact_id (single vendor), check total
            total_outstanding = sum(float(safe_get(inv, "due", 0)) for inv in invoices)

            if total_outstanding < min_outstanding:
                vendor_display = vendor_name or f"contact_id={resolved_contact_id}" if resolved_contact_id else "all vendors"
                return (
                    f"Vendor '{vendor_display}' has total outstanding "
                    f"{format_currency(total_outstanding)}, which is below the minimum "
                    f"threshold of {format_currency(min_outstanding)}."
                )

        # If no results and search_term looks like a company name, try client-side fuzzy search
        if not invoices and search_term and len(search_term) >= 3:
            # Fetch more invoices without search filter for client-side matching
            broader_data = await client.get(
                "purchase_invoices",
                "list",
                params={
                    "search": "",
                    "contact_id": args.get("contact_id"),
                    "status_id": args.get("status_id"),
                    "date_from": date_from,
                    "date_to": date_to,
                    "due_date_from": due_date_from,
                    "due_date_to": due_date_to,
                    "per_page": 100
                },
                cache_category="invoices"
            )
            all_invoices = safe_get(broader_data, "data.data", [])

            # Try fuzzy company name matching
            invoices = filter_invoices_by_company_fuzzy(all_invoices, search_term)

            # Apply client-side overdue filtering
            if is_overdue_query and invoices:
                invoices = [inv for inv in invoices if float(safe_get(inv, "due", 0)) > 0 and safe_get(inv, "status_id") != 3]

            if invoices:
                # Found matches via client-side fuzzy search
                result.append(f"_Note: Results found via fuzzy vendor name matching for '{search_term}'_\n")
            else:
                result.append("No purchase invoices found.")
                return "\n".join(result)
        elif not invoices:
            result.append("No purchase invoices found.")
            return "\n".join(result)

        result.append(f"**Total Found**: {len(invoices)}\n")

        total_gross_amount = sum(float(safe_get(inv, "amount_after_tax", 0)) for inv in invoices)
        total_due = sum(float(safe_get(inv, "due", 0)) for inv in invoices)
        total_paid = total_gross_amount - total_due

        result.append(f"**Gross Amount (Total)**: {format_currency(total_gross_amount)}")
        result.append(f"**Total Paid**: {format_currency(total_paid)}")
        result.append(f"**Total Outstanding**: {format_currency(total_due)}\n")

        # Add aging bucket display if in overdue mode
        if is_overdue_query:
            today_jakarta = get_jakarta_today()
            buckets = categorize_overdue_invoices(invoices, today_jakarta)
            result.append("\n## Overdue Aging:\n")

            # Calculate totals for each bucket
            for bucket_name in ["1-30", "31-60", "60+"]:
                bucket_items = buckets[bucket_name]
                if bucket_items:
                    bucket_count = len(bucket_items)
                    bucket_outstanding = sum(float(safe_get(inv, "due", 0)) for inv, _ in bucket_items)
                    result.append(f"**{bucket_name} hari**: {bucket_count} invoices, {format_currency(bucket_outstanding)} outstanding")

            result.append("")  # Empty line

        result.append("\n## Purchase Invoices:\n")

        # Status mapping (VERIFIED from dashboard - purchase invoices only have status 1 and 3)
        status_map = {
            1: "Belum Dibayar (Unpaid)",
            3: "Lunas (Paid)"
        }

        for invoice in invoices[:20]:
            inv_number = safe_get(invoice, "ref_number", "N/A")
            vendor = format_customer_display(invoice)  # Show company name + contact
            date = safe_get(invoice, "trans_date", "")
            due_date = safe_get(invoice, "due_date", "")
            amount = float(safe_get(invoice, "amount_after_tax", 0))
            due = float(safe_get(invoice, "due", 0))
            paid = amount - due
            status_id = safe_get(invoice, "status_id", 0)
            status = status_map.get(status_id, f"Status-{status_id}")

            result.append(f"### {inv_number}")
            result.append(f"- **Vendor**: {vendor}")
            result.append(f"- **Date**: {date}")
            if due_date:
                result.append(f"- **Due Date**: {due_date}")
                # Show overdue days if in overdue mode
                if is_overdue_query:
                    today_jakarta = get_jakarta_today()
                    overdue_days_count = calculate_overdue_days(due_date, today_jakarta)
                    if overdue_days_count > 0:
                        result.append(f"- **Overdue**: {overdue_days_count} hari")
            result.append(f"- **Gross Amount**: {format_currency(amount)}")
            result.append(f"- **Paid**: {format_currency(paid)}")
            result.append(f"- **Outstanding**: {format_currency(due)}")
            result.append(f"- **Status**: {status}\n")

        if len(invoices) > 20:
            result.append(f"... and {len(invoices) - 20} more invoices")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching purchase invoices: {str(e)}"
