"""
Account entity model.
"""
from decimal import Decimal
from typing import Optional

from pydantic import Field

from .base import BaseEntity


class Account(BaseEntity):
    """Bank/cash account."""

    name: str = Field(description="Account name (e.g., 'BCA Checking')")
    account_number: Optional[str] = Field(
        default=None,
        description="Bank account number"
    )
    balance: Decimal = Field(default=Decimal("0"), description="Current balance")
    currency: str = Field(default="IDR", description="Currency code (ISO 4217)")
    account_type: Optional[str] = Field(
        default=None,
        description="Account type (e.g., 'bank', 'cash', 'credit_card')"
    )
    is_active: bool = Field(default=True, description="Whether account is active")
