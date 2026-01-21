"""
Invoice entity models.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseEntity


class InvoiceItem(BaseModel):
    """Line item within an invoice."""

    product_id: Optional[int] = Field(
        default=None,
        description="Product reference",
        json_schema_extra={"relationship": {"target": "Product", "type": "many-to-one"}}
    )
    desc: str = Field(description="Item description")
    qty: Decimal = Field(description="Quantity")
    price: Decimal = Field(description="Unit price")
    amount: Decimal = Field(description="Line total (qty * price)")


class Invoice(BaseEntity):
    """Sales or Purchase invoice."""

    trans_number: str = Field(description="Invoice number (e.g., INV-2026-0001)")
    trans_date: date = Field(description="Invoice date")
    due_date: Optional[date] = Field(default=None, description="Payment due date")
    contact_id: int = Field(
        description="Customer/vendor reference",
        json_schema_extra={"relationship": {"target": "Contact", "type": "many-to-one"}}
    )
    contact_name: Optional[str] = Field(
        default=None,
        description="Denormalized contact name"
    )
    status_id: int = Field(description="Invoice status ID")
    status_name: Optional[str] = Field(
        default=None,
        description="Denormalized status name"
    )
    subtotal: Decimal = Field(
        default=Decimal("0"),
        description="Sum of line items before tax"
    )
    tax_amount: Decimal = Field(default=Decimal("0"), description="Total tax amount")
    grand_total: Decimal = Field(
        default=Decimal("0"),
        description="Total including tax"
    )
    amount_paid: Decimal = Field(
        default=Decimal("0"),
        description="Amount already paid"
    )
    detail: list[InvoiceItem] = Field(
        default_factory=list,
        description="Invoice line items",
        json_schema_extra={"relationship": {"target": "InvoiceItem", "type": "one-to-many", "embedded": True}}
    )
    memo: Optional[str] = Field(default=None, description="Internal notes")
