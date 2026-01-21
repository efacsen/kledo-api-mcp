"""
Order entity models.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseEntity


class OrderItem(BaseModel):
    """Line item within an order."""

    product_id: Optional[int] = Field(
        default=None,
        description="Product reference",
        json_schema_extra={"relationship": {"target": "Product", "type": "many-to-one"}}
    )
    desc: str = Field(description="Item description")
    qty: Decimal = Field(description="Quantity ordered")
    price: Decimal = Field(description="Unit price")
    amount: Decimal = Field(description="Line total")


class Order(BaseEntity):
    """Sales or Purchase order."""

    trans_number: str = Field(description="Order number (e.g., SO-2026-0001)")
    trans_date: date = Field(description="Order date")
    contact_id: int = Field(
        description="Customer (sales) or Vendor (purchase) reference",
        json_schema_extra={"relationship": {"target": "Contact", "type": "many-to-one"}}
    )
    contact_name: Optional[str] = Field(default=None, description="Denormalized contact name")
    status_id: int = Field(description="Order status ID")
    status_name: Optional[str] = Field(default=None, description="Denormalized status name")
    subtotal: Decimal = Field(default=Decimal("0"), description="Sum of line items")
    grand_total: Decimal = Field(default=Decimal("0"), description="Total including adjustments")
    detail: list[OrderItem] = Field(
        default_factory=list,
        description="Order line items",
        json_schema_extra={"relationship": {"target": "OrderItem", "type": "one-to-many", "embedded": True}}
    )
    order_type: str = Field(
        default="sales",
        description="Order type: 'sales' or 'purchase'",
        json_schema_extra={"enum_values": ["sales", "purchase"]}
    )
