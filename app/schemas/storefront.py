"""Storefront schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class StorefrontBase(BaseModel):
    """Base storefront fields."""

    name: str = Field(min_length=1, max_length=255, description="Storefront display name")
    domain: Optional[str] = Field(default=None, max_length=255, description="Primary domain")
    description: Optional[str] = Field(default=None, description="Optional description")


class StorefrontCreate(StorefrontBase):
    """Schema for creating a storefront."""

    storefront_id: str = Field(
        min_length=1,
        max_length=50,
        description="Unique external storefront identifier",
    )
    is_active: bool = Field(default=True, description="Whether storefront is active")

    @field_validator("storefront_id")
    @classmethod
    def validate_storefront_id(cls, v: str) -> str:
        """Validate storefront_id format."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("storefront_id must be alphanumeric (hyphens and underscores allowed)")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "storefront_id": "store-123",
                "name": "My Online Store",
                "domain": "mystore.com",
                "description": "Main e-commerce storefront",
                "is_active": True,
            }
        }


class StorefrontUpdate(BaseModel):
    """Schema for updating a storefront."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    domain: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Store Name",
                "is_active": False,
            }
        }


class StorefrontResponse(BaseModel):
    """Storefront response schema."""

    id: int
    storefront_id: str
    name: str
    domain: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "storefront_id": "store-123",
                "name": "My Online Store",
                "domain": "mystore.com",
                "description": "Main e-commerce storefront",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }
