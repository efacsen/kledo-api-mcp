"""Invoice financial domain model with clear business terminology.

This module converts confusing Kledo API field names to standard accounting terms:
- Kledo 'subtotal' -> net_sales (Penjualan Neto, revenue before tax)
- Kledo 'total_tax' -> tax_collected (PPN collected)
- Kledo 'amount_after_tax' -> gross_sales (Penjualan Bruto, total with tax)
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InvoiceFinancials(BaseModel):
    """Financial data for a single invoice with clear business terminology.

    This domain model converts confusing Kledo API field names to standard
    accounting terminology:

    Kledo API -> Domain Model:
    - subtotal -> net_sales (Penjualan Neto, revenue before tax)
    - total_tax -> tax_collected (PPN collected)
    - amount_after_tax -> gross_sales (Penjualan Bruto, total with tax)

    The mathematical relationship is:
        net_sales + tax_collected = gross_sales

    This is validated on instantiation to ensure data integrity.
    """

    model_config = ConfigDict(frozen=True)  # Immutable after creation

    net_sales: Decimal = Field(
        description="Revenue before tax (Penjualan Neto). Source: Kledo 'subtotal'"
    )
    tax_collected: Decimal = Field(
        description="Tax amount collected (PPN). Source: Kledo 'total_tax'"
    )
    gross_sales: Decimal = Field(
        description="Total including tax (Penjualan Bruto). Source: Kledo 'amount_after_tax'"
    )

    # Optional metadata for traceability
    invoice_id: Optional[int] = Field(default=None, description="Source invoice ID")
    ref_number: Optional[str] = Field(
        default=None, description="Invoice reference number"
    )

    @model_validator(mode="after")
    def validate_financial_integrity(self) -> "InvoiceFinancials":
        """Validate that net_sales + tax_collected = gross_sales.

        Allows small tolerance (Rp 1) for rounding differences in Kledo API.
        """
        expected = self.net_sales + self.tax_collected
        tolerance = Decimal("1")  # 1 rupiah tolerance
        difference = abs(expected - self.gross_sales)

        if difference > tolerance:
            raise ValueError(
                f"Financial integrity error: "
                f"net_sales ({self.net_sales:,.0f}) + "
                f"tax_collected ({self.tax_collected:,.0f}) = "
                f"{expected:,.0f}, but gross_sales is {self.gross_sales:,.0f}. "
                f"Difference: {difference:,.0f}"
            )
        return self

    @property
    def tax_rate(self) -> Decimal:
        """Calculate effective tax rate as percentage."""
        if self.net_sales == 0:
            return Decimal("0")
        return (self.tax_collected / self.net_sales) * 100
