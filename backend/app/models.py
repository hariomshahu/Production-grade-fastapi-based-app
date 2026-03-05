"""Pydantic models for Items CRUD."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Payload for creating an item."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class ItemUpdate(BaseModel):
    """Payload for updating an item (partial allowed in logic)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class Item(BaseModel):
    """Item as returned by API."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
