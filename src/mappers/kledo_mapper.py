"""Mapper functions to convert Kledo API data to domain models.

This module handles the field name mapping from Kledo API fields to clear
business terminology:
- Kledo 'subtotal' -> domain 'net_sales'
- Kledo 'total_tax' -> domain 'tax_collected'
- Kledo 'amount_after_tax' -> domain 'gross_sales'
"""

from decimal import Decimal, InvalidOperation
from typing import Any

from src.models.invoice_financials import InvoiceFinancials


def from_kledo_invoice(
    kledo_data: dict[str, Any],
    include_metadata: bool = True,
) -> InvoiceFinancials:
    """Convert a single Kledo invoice API response to domain model.

    This function handles the field name mapping:
    - Kledo 'subtotal' -> domain 'net_sales'
    - Kledo 'total_tax' -> domain 'tax_collected'
    - Kledo 'amount_after_tax' -> domain 'gross_sales'

    Args:
        kledo_data: Raw invoice dict from Kledo API response
        include_metadata: If True, include invoice_id and ref_number

    Returns:
        InvoiceFinancials domain model with validated data

    Raises:
        ValueError: If data validation fails (e.g., integrity check)
        KeyError: If required field is missing from kledo_data

    Example:
        >>> inv = from_kledo_invoice({
        ...     "subtotal": 16320000,
        ...     "total_tax": 1795200,
        ...     "amount_after_tax": 18115200,
        ...     "id": 123,
        ...     "ref_number": "INV/26/JAN/01153"
        ... })
        >>> inv.net_sales
        Decimal('16320000')
    """
    # CRITICAL: Convert to str before Decimal to avoid float precision issues
    # Kledo API may return int or float, str() handles both safely

    try:
        net_sales = Decimal(str(kledo_data["subtotal"]))
        tax_collected = Decimal(str(kledo_data["total_tax"]))
        gross_sales = Decimal(str(kledo_data["amount_after_tax"]))
    except (InvalidOperation, TypeError) as e:
        raise ValueError(f"Invalid numeric value in invoice data: {e}")

    kwargs: dict[str, Any] = {
        "net_sales": net_sales,
        "tax_collected": tax_collected,
        "gross_sales": gross_sales,
    }

    if include_metadata:
        kwargs["invoice_id"] = kledo_data.get("id")
        kwargs["ref_number"] = kledo_data.get("ref_number")

    return InvoiceFinancials(**kwargs)


def from_kledo_invoices(
    kledo_invoices: list[dict[str, Any]],
    skip_invalid: bool = False,
    include_metadata: bool = True,
) -> list[InvoiceFinancials]:
    """Convert list of Kledo invoices to domain models.

    Args:
        kledo_invoices: List of raw invoice dicts from Kledo API
        skip_invalid: If True, skip invalid invoices with warning;
                      if False, raise on first error
        include_metadata: If True, include invoice_id and ref_number

    Returns:
        List of InvoiceFinancials domain models

    Example:
        >>> invoices = from_kledo_invoices(api_response["data"]["data"])
        >>> total_gross = sum(inv.gross_sales for inv in invoices)
    """
    results: list[InvoiceFinancials] = []

    for i, inv in enumerate(kledo_invoices):
        try:
            results.append(from_kledo_invoice(inv, include_metadata))
        except (ValueError, KeyError) as e:
            if not skip_invalid:
                ref = inv.get("ref_number", f"index {i}")
                raise ValueError(f"Failed to convert invoice {ref}: {e}") from e
            # If skip_invalid, continue to next invoice

    return results


def aggregate_financials(invoices: list[InvoiceFinancials]) -> InvoiceFinancials:
    """Aggregate multiple invoices into a single financial summary.

    Useful for period summaries (monthly revenue, etc.).

    Args:
        invoices: List of InvoiceFinancials to aggregate

    Returns:
        InvoiceFinancials with summed values (no metadata)
    """
    if not invoices:
        return InvoiceFinancials(
            net_sales=Decimal("0"),
            tax_collected=Decimal("0"),
            gross_sales=Decimal("0"),
        )

    return InvoiceFinancials(
        net_sales=sum(inv.net_sales for inv in invoices),
        tax_collected=sum(inv.tax_collected for inv in invoices),
        gross_sales=sum(inv.gross_sales for inv in invoices),
    )
