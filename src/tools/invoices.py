"""
Invoice tools for Kledo MCP Server
"""
import re
from typing import Any, Dict
from mcp.types import Tool
from rapidfuzz import fuzz

from ..kledo_client import KledoAPIClient
from ..utils.helpers import parse_date_range, format_currency, safe_get


def format_customer_display(invoice: dict) -> str:
    """
    Format customer/vendor display name prioritizing company name.
    
    For B2B context (PT CSS), company name is more important than contact person name.
    
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
                        "description": "Start date (YYYY-MM-DD or 'last_month', 'this_month', etc.)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 50, max: 100)"
                    },
                    "invoice_selection": {
                        "type": "integer",
                        "description": "When fuzzy search returns multiple matches, use this to select a specific invoice by number (1-based index). Will be shown when multiple fuzzy matches are found."
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
            description="List purchase invoices (bills from vendors) with optional filtering. Displays vendor company name prominently for B2B vendors.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search term for vendor name or company name. Supports fuzzy matching (e.g., 'Nipsea' → 'PT Nippon Paint Indonesia')"
                    },
                    "contact_id": {
                        "type": "integer",
                        "description": "Filter by vendor ID"
                    },
                    "status_id": {
                        "type": "integer",
                        "description": "Filter by status"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date"
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 50)"
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
    else:
        return f"Unknown invoice tool: {name}"


async def _list_sales_invoices(args: Dict[str, Any], client: KledoAPIClient) -> str:
    """List sales invoices."""
    # Parse date range
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    if date_from and not date_to:
        parsed_from, parsed_to = parse_date_range(date_from)
        if parsed_from:
            date_from = parsed_from
            date_to = parsed_to

    search_term = args.get("search", "").strip()
    fuzzy_search = should_use_fuzzy_search(search_term)
    invoice_selection = args.get("invoice_selection")

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
                per_page=200,  # Fetch more invoices for fuzzy matching
                force_refresh=args.get("force_refresh", False)
            )

            all_invoices = safe_get(data, "data.data", [])

            # Apply fuzzy filtering
            invoices = filter_invoices_by_fuzzy_search(all_invoices, search_term)

            if not invoices:
                return f"No invoices found matching fuzzy search for '{search_term}'."

            # Handle invoice selection if specified
            if invoice_selection is not None:
                try:
                    selection_idx = int(invoice_selection) - 1  # Convert to 0-based index
                    if 0 <= selection_idx < len(invoices):
                        invoices = [invoices[selection_idx]]
                    else:
                        return f"Invalid invoice selection {invoice_selection}. Please choose a number between 1-{len(invoices)}."
                except (ValueError, TypeError):
                    return "Invalid invoice selection. Please provide a number."
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
                per_page=args.get("per_page", 50),
                force_refresh=args.get("force_refresh", False)
            )
            invoices = safe_get(data, "data.data", [])

            # If no results and search_term looks like a company name, try client-side fuzzy search
            if not invoices and search_term and len(search_term) >= 3:
                # Fetch more invoices without search filter for client-side matching
                broader_data = await client.list_invoices(
                    search="",
                    contact_id=args.get("contact_id"),
                    status_id=args.get("status_id"),
                    date_from=date_from,
                    date_to=date_to,
                    per_page=100,
                    force_refresh=args.get("force_refresh", False)
                )
                all_invoices = safe_get(broader_data, "data.data", [])
                
                # Try fuzzy company name matching
                invoices = filter_invoices_by_company_fuzzy(all_invoices, search_term)
                
                if invoices:
                    # Found matches via client-side fuzzy search
                    result = ["# Sales Invoices\n"]
                    result.append(f"_Note: Results found via fuzzy company name matching for '{search_term}'_\n")
                else:
                    result = ["# Sales Invoices\n"]
                    result.append("No invoices found matching the criteria.")
                    return "\n".join(result)
            elif not invoices:
                result = ["# Sales Invoices\n"]
                result.append("No invoices found matching the criteria.")
                return "\n".join(result)

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


def _handle_fuzzy_search_disambiguation(invoices: list[dict], search_term: str) -> str:
    """
    Present multiple fuzzy search matches for user to choose from.

    Args:
        invoices: List of matching invoices (sorted by match quality)
        search_term: The original search term that triggered fuzzy search

    Returns:
        Formatted string showing options and instructions for selection
    """
    result = ["# Fuzzy Search Results\n"]

    result.append(f"**Search Term**: '{search_term}'")
    result.append(f"**Multiple Matches Found**: {len(invoices)}\n")

    result.append("## Matching Invoices:\n")

    # Status mapping (VERIFIED from dashboard)
    status_map = {
        1: "Belum Dibayar (Unpaid)",
        2: "Dibayar Sebagian (Partially Paid)",
        3: "Lunas (Paid)"
    }

    # Show up to 15 matches
    for i, invoice in enumerate(invoices[:15], 1):
        inv_number = safe_get(invoice, "ref_number", "N/A")
        customer = format_customer_display(invoice)  # Show company name + contact
        date = safe_get(invoice, "trans_date", "")
        amount_after_tax = float(safe_get(invoice, "amount_after_tax", 0))
        due = float(safe_get(invoice, "due", 0))
        status_id = safe_get(invoice, "status_id", 0)
        status = status_map.get(status_id, f"Status-{status_id}")

        # Extract the matching part from the invoice number for highlighting
        best_match_highlight = _get_best_match_highlight(search_term, inv_number)

        result.append(f"### [{i}] {inv_number}")
        result.append(f"**Best Match**: {best_match_highlight}")
        result.append(f"- **Customer**: {customer}")
        result.append(f"- **Date**: {date}")
        result.append(f"- **Amount**: {format_currency(amount_after_tax)}")
        result.append(f"- **Outstanding**: {format_currency(due)}")
        result.append(f"- **Status**: {status}\n")

    if len(invoices) > 15:
        result.append(f"... and {len(invoices) - 15} more matches\n")

    result.append("## Select Invoice")
    result.append("To view a specific invoice, call the tool again with the same search term and add:")
    result.append(f'- `invoice_selection: <number>` (where <number> is 1-{len(invoices)})\n')
    result.append("Example:")
    result.append(f'`{{"search": "{search_term}", "invoice_selection": 1}}`')

    # Show most recent invoice as a suggestion
    most_recent = max(invoices, key=lambda inv: safe_get(inv, "trans_date", ""))
    recent_number = safe_get(most_recent, "ref_number", "Unknown")
    result.append(f"\n**Tip**: Most recent matching invoice is `{recent_number}` (call with `invoice_selection: 1` to view)")

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

    try:
        data = await client.get(
            "purchase_invoices",
            "list",
            params={
                "search": search_term,
                "contact_id": args.get("contact_id"),
                "status_id": args.get("status_id"),
                "date_from": date_from,
                "date_to": date_to,
                "per_page": args.get("per_page", 50)
            },
            cache_category="invoices"
        )

        result = ["# Purchase Invoices\n"]

        invoices = safe_get(data, "data.data", [])

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
                    "per_page": 100
                },
                cache_category="invoices"
            )
            all_invoices = safe_get(broader_data, "data.data", [])
            
            # Try fuzzy company name matching
            invoices = filter_invoices_by_company_fuzzy(all_invoices, search_term)
            
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
            amount = float(safe_get(invoice, "amount_after_tax", 0))
            due = float(safe_get(invoice, "due", 0))
            paid = amount - due
            status_id = safe_get(invoice, "status_id", 0)
            status = status_map.get(status_id, f"Status-{status_id}")

            result.append(f"### {inv_number}")
            result.append(f"- **Vendor**: {vendor}")
            result.append(f"- **Date**: {date}")
            result.append(f"- **Gross Amount**: {format_currency(amount)}")
            result.append(f"- **Paid**: {format_currency(paid)}")
            result.append(f"- **Outstanding**: {format_currency(due)}")
            result.append(f"- **Status**: {status}\n")

        if len(invoices) > 20:
            result.append(f"... and {len(invoices) - 20} more invoices")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching purchase invoices: {str(e)}"
