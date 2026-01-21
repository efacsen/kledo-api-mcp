"""
Contact entity model.
"""
from decimal import Decimal
from typing import Optional

from pydantic import Field

from .base import BaseEntity


class Contact(BaseEntity):
    """Customer or Vendor contact."""

    name: str = Field(description="Contact's full name")
    company: Optional[str] = Field(default=None, description="Company/organization name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    address: Optional[str] = Field(default=None, description="Physical address")
    type_id: int = Field(
        description="Contact type: 1=Customer, 2=Vendor, 3=Both",
        json_schema_extra={"enum_values": {1: "Customer", 2: "Vendor", 3: "Both"}}
    )
    type_name: Optional[str] = Field(default=None, description="Denormalized type name")
    total_receivable: Decimal = Field(
        default=Decimal("0"),
        description="Amount owed by this contact"
    )
    total_payable: Decimal = Field(
        default=Decimal("0"),
        description="Amount owed to this contact"
    )
