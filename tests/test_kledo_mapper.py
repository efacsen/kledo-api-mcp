"""Tests for the Kledo to domain model mapper.

These tests verify the conversion from Kledo API field names to clear
business terminology:
- subtotal -> net_sales
- total_tax -> tax_collected
- amount_after_tax -> gross_sales
"""

import pytest
from decimal import Decimal

from src.models.invoice_financials import InvoiceFinancials
from src.mappers.kledo_mapper import (
    from_kledo_invoice,
    from_kledo_invoices,
    aggregate_financials,
)


# Test data based on validated real invoices (see tests/validate_invoice_fields.py)
VALID_INVOICE_DATA = {
    "id": 12345,
    "ref_number": "INV/26/JAN/01153",
    "subtotal": 16320000,
    "total_tax": 1795200,
    "amount_after_tax": 18115200,
}

VALID_ZERO_TAX_DATA = {
    "id": 12346,
    "ref_number": "INV/26/JAN/01154",
    "subtotal": 4410000,
    "total_tax": 0,
    "amount_after_tax": 4410000,
}


class TestInvoiceFinancialsModel:
    """Tests for the InvoiceFinancials Pydantic model."""

    def test_creates_valid_model(self):
        """Creates model with valid data."""
        inv = InvoiceFinancials(
            net_sales=Decimal("16320000"),
            tax_collected=Decimal("1795200"),
            gross_sales=Decimal("18115200"),
        )

        assert inv.net_sales == Decimal("16320000")
        assert inv.tax_collected == Decimal("1795200")
        assert inv.gross_sales == Decimal("18115200")

    def test_validates_integrity(self):
        """Raises ValueError when net + tax != gross."""
        with pytest.raises(ValueError, match="Financial integrity error"):
            InvoiceFinancials(
                net_sales=Decimal("1000"),
                tax_collected=Decimal("100"),
                gross_sales=Decimal("9999"),
            )

    def test_calculates_tax_rate(self):
        """Tax rate property calculates correctly."""
        inv = InvoiceFinancials(
            net_sales=Decimal("16320000"),
            tax_collected=Decimal("1795200"),
            gross_sales=Decimal("18115200"),
        )

        # 1795200 / 16320000 * 100 = 11% (Indonesian PPN)
        assert inv.tax_rate == Decimal("11")

    def test_handles_zero_tax(self):
        """Zero tax does not cause division errors."""
        inv = InvoiceFinancials(
            net_sales=Decimal("4410000"),
            tax_collected=Decimal("0"),
            gross_sales=Decimal("4410000"),
        )

        assert inv.tax_rate == Decimal("0")
        assert inv.tax_collected == Decimal("0")

    def test_model_is_immutable(self):
        """Frozen config prevents modification."""
        inv = InvoiceFinancials(
            net_sales=Decimal("1000"),
            tax_collected=Decimal("100"),
            gross_sales=Decimal("1100"),
        )

        with pytest.raises(Exception):
            inv.net_sales = Decimal("2000")

    def test_handles_zero_net_sales_for_tax_rate(self):
        """Zero net_sales returns 0% tax rate without division error."""
        inv = InvoiceFinancials(
            net_sales=Decimal("0"),
            tax_collected=Decimal("0"),
            gross_sales=Decimal("0"),
        )

        assert inv.tax_rate == Decimal("0")


class TestFromKledoInvoice:
    """Tests for single invoice conversion."""

    def test_converts_valid_invoice(self):
        """Converts valid Kledo invoice to domain model."""
        result = from_kledo_invoice(VALID_INVOICE_DATA)

        assert result.net_sales == Decimal("16320000")
        assert result.tax_collected == Decimal("1795200")
        assert result.gross_sales == Decimal("18115200")
        assert result.invoice_id == 12345
        assert result.ref_number == "INV/26/JAN/01153"

    def test_converts_zero_tax_invoice(self):
        """Handles invoices with zero tax correctly."""
        result = from_kledo_invoice(VALID_ZERO_TAX_DATA)

        assert result.net_sales == Decimal("4410000")
        assert result.tax_collected == Decimal("0")
        assert result.gross_sales == Decimal("4410000")

    def test_includes_metadata(self):
        """Invoice_id and ref_number are captured when include_metadata=True."""
        result = from_kledo_invoice(VALID_INVOICE_DATA, include_metadata=True)

        assert result.invoice_id == 12345
        assert result.ref_number == "INV/26/JAN/01153"

    def test_excludes_metadata_when_requested(self):
        """Can exclude metadata from conversion."""
        result = from_kledo_invoice(VALID_INVOICE_DATA, include_metadata=False)

        assert result.invoice_id is None
        assert result.ref_number is None

    def test_raises_on_missing_field(self):
        """Raises KeyError when required field is missing."""
        invalid_data = {"subtotal": 1000, "total_tax": 100}  # missing amount_after_tax

        with pytest.raises(KeyError):
            from_kledo_invoice(invalid_data)

    def test_raises_on_integrity_failure(self):
        """Raises ValueError when net + tax != gross."""
        bad_data = {
            "subtotal": 1000,
            "total_tax": 100,
            "amount_after_tax": 9999,  # Should be 1100
        }

        with pytest.raises(ValueError, match="Financial integrity error"):
            from_kledo_invoice(bad_data)

    def test_handles_float_values_safely(self):
        """Handles float values from API without precision loss."""
        float_data = {
            "subtotal": 16320000.0,  # Float, not int
            "total_tax": 1795200.0,
            "amount_after_tax": 18115200.0,
        }

        result = from_kledo_invoice(float_data, include_metadata=False)
        assert result.net_sales == Decimal("16320000")

    def test_handles_string_values(self):
        """Handles string numeric values from API."""
        string_data = {
            "subtotal": "16320000",
            "total_tax": "1795200",
            "amount_after_tax": "18115200",
        }

        result = from_kledo_invoice(string_data, include_metadata=False)
        assert result.net_sales == Decimal("16320000")

    def test_calculates_tax_rate(self):
        """Computed tax_rate property works correctly."""
        result = from_kledo_invoice(VALID_INVOICE_DATA)

        # 1795200 / 16320000 * 100 = 11% (Indonesian PPN)
        assert result.tax_rate == Decimal("11")


class TestFromKledoInvoices:
    """Tests for batch invoice conversion."""

    def test_converts_multiple_invoices(self):
        """Converts list of invoices correctly."""
        invoices = [VALID_INVOICE_DATA, VALID_ZERO_TAX_DATA]

        results = from_kledo_invoices(invoices)

        assert len(results) == 2
        assert results[0].net_sales == Decimal("16320000")
        assert results[1].net_sales == Decimal("4410000")

    def test_skips_invalid_when_requested(self):
        """Skips invalid invoices when skip_invalid=True."""
        bad_data = {"subtotal": 1000, "total_tax": 100, "amount_after_tax": 9999}
        invoices = [VALID_INVOICE_DATA, bad_data, VALID_ZERO_TAX_DATA]

        results = from_kledo_invoices(invoices, skip_invalid=True)

        assert len(results) == 2  # Bad one skipped

    def test_raises_on_invalid_by_default(self):
        """Raises on invalid invoice when skip_invalid=False."""
        bad_data = {"subtotal": 1000, "total_tax": 100, "amount_after_tax": 9999}
        invoices = [VALID_INVOICE_DATA, bad_data]

        with pytest.raises(ValueError, match="Failed to convert invoice"):
            from_kledo_invoices(invoices, skip_invalid=False)

    def test_handles_empty_list(self):
        """Returns empty list for empty input."""
        results = from_kledo_invoices([])

        assert results == []

    def test_preserves_order(self):
        """Invoices maintain order after conversion."""
        invoices = [VALID_INVOICE_DATA, VALID_ZERO_TAX_DATA]

        results = from_kledo_invoices(invoices)

        assert results[0].invoice_id == 12345
        assert results[1].invoice_id == 12346


class TestAggregateFinancials:
    """Tests for aggregation function."""

    def test_aggregates_multiple_invoices(self):
        """Sums financial values correctly."""
        inv1 = from_kledo_invoice(VALID_INVOICE_DATA, include_metadata=False)
        inv2 = from_kledo_invoice(VALID_ZERO_TAX_DATA, include_metadata=False)

        result = aggregate_financials([inv1, inv2])

        assert result.net_sales == Decimal("20730000")  # 16320000 + 4410000
        assert result.tax_collected == Decimal("1795200")  # 1795200 + 0
        assert result.gross_sales == Decimal("22525200")  # 18115200 + 4410000

    def test_returns_zeros_for_empty_list(self):
        """Returns zero values for empty invoice list."""
        result = aggregate_financials([])

        assert result.net_sales == Decimal("0")
        assert result.tax_collected == Decimal("0")
        assert result.gross_sales == Decimal("0")

    def test_aggregate_has_no_metadata(self):
        """Aggregated result has no invoice_id or ref_number."""
        inv1 = from_kledo_invoice(VALID_INVOICE_DATA)

        result = aggregate_financials([inv1])

        assert result.invoice_id is None
        assert result.ref_number is None

    def test_single_invoice_aggregation(self):
        """Single invoice aggregation returns same values."""
        inv = from_kledo_invoice(VALID_INVOICE_DATA, include_metadata=False)

        result = aggregate_financials([inv])

        assert result.net_sales == inv.net_sales
        assert result.tax_collected == inv.tax_collected
        assert result.gross_sales == inv.gross_sales
