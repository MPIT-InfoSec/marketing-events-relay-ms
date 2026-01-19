"""Platform schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.enums import AuthType


class PlatformBase(BaseModel):
    """Base platform fields."""

    name: str = Field(min_length=1, max_length=100, description="Platform display name")
    category: str = Field(default="advertising", max_length=50, description="Platform category")
    tier: int = Field(default=3, ge=1, le=3, description="Priority tier: 1=critical, 2=important, 3=standard")
    auth_type: AuthType = Field(default=AuthType.ACCESS_TOKEN, description="Authentication type")
    api_base_url: Optional[str] = Field(default=None, max_length=500, description="Base URL for API")
    credential_schema: Optional[str] = Field(default=None, description="JSON schema for credentials")
    description: Optional[str] = Field(default=None, description="Platform description")


class PlatformCreate(PlatformBase):
    """Schema for creating a platform."""

    platform_code: str = Field(
        min_length=1,
        max_length=50,
        description="Unique platform code",
    )
    is_active: bool = Field(default=True, description="Whether platform is active")

    @field_validator("platform_code")
    @classmethod
    def validate_platform_code(cls, v: str) -> str:
        """Validate platform_code format."""
        if not v.replace("_", "").isalnum():
            raise ValueError("platform_code must be alphanumeric with underscores only")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "platform_code": "custom_platform",
                "name": "Custom Ad Platform",
                "category": "advertising",
                "tier": 3,
                "auth_type": "access_token",
                "api_base_url": "https://api.customplatform.com",
                "credential_schema": '{"access_token": "string"}',
                "description": "Custom advertising platform",
                "is_active": True,
            }
        }


class PlatformUpdate(BaseModel):
    """Schema for updating a platform."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)
    tier: Optional[int] = Field(default=None, ge=1, le=3)
    auth_type: Optional[AuthType] = None
    api_base_url: Optional[str] = Field(default=None, max_length=500)
    credential_schema: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "tier": 2,
                "is_active": False,
            }
        }


class PlatformResponse(BaseModel):
    """Platform response schema."""

    id: int
    platform_code: str
    name: str
    category: str
    tier: int
    auth_type: AuthType
    api_base_url: Optional[str]
    credential_schema: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "platform_code": "meta_capi",
                "name": "Meta Conversions API",
                "category": "advertising",
                "tier": 1,
                "auth_type": "access_token",
                "api_base_url": "https://graph.facebook.com/v18.0",
                "credential_schema": '{"access_token": "string", "pixel_id": "string"}',
                "description": "Meta Conversions API for Facebook/Instagram",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }
