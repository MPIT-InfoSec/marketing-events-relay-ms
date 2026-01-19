"""Credential schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.enums import DestinationType


class CredentialBase(BaseModel):
    """Base credential fields."""

    destination_type: DestinationType = Field(
        default=DestinationType.SGTM,
        description="Delivery method: sgtm or direct",
    )
    pixel_id: Optional[str] = Field(default=None, max_length=100, description="Platform pixel ID")
    account_id: Optional[str] = Field(default=None, max_length=100, description="Platform account ID")


class CredentialCreate(CredentialBase):
    """Schema for creating a credential."""

    storefront_id: int = Field(description="Associated storefront ID")
    platform_id: int = Field(description="Associated platform ID")
    credentials: dict[str, Any] = Field(description="Credential key-value pairs (will be encrypted)")
    is_active: bool = Field(default=True, description="Whether credential is active")

    class Config:
        json_schema_extra = {
            "example": {
                "storefront_id": 1,
                "platform_id": 1,
                "credentials": {
                    "access_token": "EAAxxxxxxxx",
                    "pixel_id": "123456789",
                },
                "destination_type": "sgtm",
                "pixel_id": "123456789",
                "account_id": "act_123456",
                "is_active": True,
            }
        }


class CredentialUpdate(BaseModel):
    """Schema for updating a credential."""

    credentials: Optional[dict[str, Any]] = Field(default=None, description="New credentials")
    destination_type: Optional[DestinationType] = None
    pixel_id: Optional[str] = Field(default=None, max_length=100)
    account_id: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "credentials": {
                    "access_token": "new_token_here",
                },
                "is_active": False,
            }
        }


class CredentialResponse(BaseModel):
    """Credential response schema (without decrypted credentials)."""

    id: int
    storefront_id: int
    platform_id: int
    destination_type: DestinationType
    pixel_id: Optional[str]
    account_id: Optional[str]
    is_active: bool
    last_used_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Nested info
    platform_code: Optional[str] = None
    platform_name: Optional[str] = None
    storefront_name: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "storefront_id": 1,
                "platform_id": 1,
                "destination_type": "sgtm",
                "pixel_id": "123456789",
                "account_id": "act_123456",
                "is_active": True,
                "last_used_at": "2024-01-01T12:00:00Z",
                "last_error": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "platform_code": "meta_capi",
                "platform_name": "Meta Conversions API",
                "storefront_name": "My Store",
            }
        }


class CredentialWithSecretsResponse(CredentialResponse):
    """Credential response with decrypted credentials (for ?decrypt=true)."""

    credentials: dict[str, Any] = Field(description="Decrypted credentials")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "storefront_id": 1,
                "platform_id": 1,
                "destination_type": "sgtm",
                "pixel_id": "123456789",
                "account_id": "act_123456",
                "is_active": True,
                "last_used_at": "2024-01-01T12:00:00Z",
                "last_error": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "platform_code": "meta_capi",
                "platform_name": "Meta Conversions API",
                "storefront_name": "My Store",
                "credentials": {
                    "access_token": "EAAxxxxxxxx",
                    "pixel_id": "123456789",
                },
            }
        }
