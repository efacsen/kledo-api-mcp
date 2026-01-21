"""
Base entity model for Kledo entities.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseEntity(BaseModel):
    """Base class for all Kledo entities."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier")
    created_at: Optional[datetime] = Field(
        default=None,
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
