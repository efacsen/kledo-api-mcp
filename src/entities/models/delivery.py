"""
Delivery entity models.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseEntity


class DeliveryItem(BaseModel):
    """Item being delivered."""

    product_id: Optional[int] = Field(
        default=None,
        description="Product reference",
        json_schema_extra={"relationship": {"target": "Product", "type": "many-to-one"}}
    )
    desc: str = Field(description="Item description")
    qty: Decimal = Field(description="Quantity being delivered")


class Delivery(BaseEntity):
    """Shipment/delivery record."""

    trans_number: str = Field(description="Delivery number (e.g., DEL-2026-0001)")
    trans_date: date = Field(description="Delivery date")
    contact_id: Optional[int] = Field(
        default=None,
        description="Customer receiving delivery",
        json_schema_extra={"relationship": {"target": "Contact", "type": "many-to-one"}}
    )
    contact_name: Optional[str] = Field(
        default=None,
        description="Denormalized contact name"
    )
    status_id: int = Field(description="Delivery status ID")
    status_name: Optional[str] = Field(
        default=None,
        description="Denormalized status name"
    )
    shipping_company_name: Optional[str] = Field(
        default=None,
        description="Carrier/shipping company"
    )
    tracking_number: Optional[str] = Field(
        default=None,
        description="Shipment tracking number"
    )
    shipping_address: Optional[str] = Field(
        default=None,
        description="Destination address"
    )
    ref_number: Optional[str] = Field(
        default=None,
        description="Reference to source order",
        json_schema_extra={"relationship": {"target": "Order", "type": "many-to-one", "via": "trans_number"}}
    )
    detail: list[DeliveryItem] = Field(
        default_factory=list,
        description="Items being delivered",
        json_schema_extra={"relationship": {"target": "DeliveryItem", "type": "one-to-many", "embedded": True}}
    )
    memo: Optional[str] = Field(default=None, description="Delivery notes")
