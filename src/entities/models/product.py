"""
Product entity models.
"""
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseEntity


class Warehouse(BaseModel):
    """Warehouse stock location."""

    name: str = Field(description="Warehouse name")
    qty: Decimal = Field(default=Decimal("0"), description="Stock quantity in this warehouse")


class Product(BaseEntity):
    """Product or service item."""

    name: str = Field(description="Product name")
    code: Optional[str] = Field(default=None, description="SKU/product code")
    description: Optional[str] = Field(default=None, description="Product description")
    price: Decimal = Field(default=Decimal("0"), description="Selling price")
    buy_price: Decimal = Field(default=Decimal("0"), description="Cost/purchase price")
    qty: Decimal = Field(default=Decimal("0"), description="Total stock quantity")
    category_id: Optional[int] = Field(
        default=None,
        description="Product category reference"
    )
    category_name: Optional[str] = Field(
        default=None,
        description="Denormalized category name"
    )
    warehouses: list[Warehouse] = Field(
        default_factory=list,
        description="Stock by warehouse",
        json_schema_extra={"relationship": {"target": "Warehouse", "type": "one-to-many", "embedded": True}}
    )
