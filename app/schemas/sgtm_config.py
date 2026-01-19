"""sGTM Config schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import SgtmClientType


class SgtmConfigBase(BaseModel):
    """Base sGTM config fields."""

    sgtm_url: str = Field(description="sGTM container base URL (e.g., https://tags.upscript.com)")
    client_type: SgtmClientType = Field(
        default=SgtmClientType.GA4,
        description="Client type: 'ga4' for GA4 Measurement Protocol, 'custom' for flexible JSON",
    )

    # GA4 Client fields
    container_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="GTM container ID (GTM-XXXXXX)",
    )
    measurement_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="GA4 Measurement ID (G-XXXXXX) - required for GA4 client type",
    )

    # Custom Client fields
    custom_endpoint_path: Optional[str] = Field(
        default="/collect",
        max_length=100,
        description="Endpoint path for custom client (e.g., /collect, /events)",
    )

    @field_validator("sgtm_url")
    @classmethod
    def validate_sgtm_url(cls, v: str) -> str:
        """Validate sGTM URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("sgtm_url must be a valid HTTP/HTTPS URL")
        return v.rstrip("/")

    @field_validator("container_id")
    @classmethod
    def validate_container_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate GTM container ID format."""
        if v and not v.startswith("GTM-"):
            raise ValueError("container_id must start with 'GTM-'")
        return v

    @field_validator("measurement_id")
    @classmethod
    def validate_measurement_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate GA4 measurement ID format."""
        if v and not v.startswith("G-"):
            raise ValueError("measurement_id must start with 'G-'")
        return v

    @field_validator("custom_endpoint_path")
    @classmethod
    def validate_custom_endpoint_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate custom endpoint path format."""
        if v and not v.startswith("/"):
            return "/" + v
        return v


class SgtmConfigCreate(SgtmConfigBase):
    """Schema for creating sGTM config."""

    storefront_id: int = Field(description="Associated storefront ID")
    api_secret: Optional[str] = Field(
        default=None,
        description="API secret for GA4 Measurement Protocol (will be encrypted)",
    )
    custom_headers: Optional[dict[str, str]] = Field(
        default=None,
        description="Custom headers to include in requests (for custom client type)",
    )
    is_active: bool = Field(default=True, description="Whether config is active")

    @model_validator(mode="after")
    def validate_client_type_fields(self) -> "SgtmConfigCreate":
        """Validate required fields based on client type."""
        if self.client_type == SgtmClientType.GA4:
            if not self.measurement_id:
                raise ValueError("measurement_id is required for GA4 client type")
        return self

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "title": "GA4 Client Example",
                    "value": {
                        "storefront_id": 1,
                        "sgtm_url": "https://tags.upscript.com",
                        "client_type": "ga4",
                        "container_id": "GTM-XXXXXX",
                        "measurement_id": "G-XXXXXX",
                        "api_secret": "secret_key_here",
                        "is_active": True,
                    },
                },
                {
                    "title": "Custom Client Example",
                    "value": {
                        "storefront_id": 1,
                        "sgtm_url": "https://tags.upscript.com",
                        "client_type": "custom",
                        "custom_endpoint_path": "/collect",
                        "custom_headers": {"X-Api-Key": "your-api-key"},
                        "is_active": True,
                    },
                },
            ]
        }


class SgtmConfigUpdate(BaseModel):
    """Schema for updating sGTM config."""

    sgtm_url: Optional[str] = None
    client_type: Optional[SgtmClientType] = None
    container_id: Optional[str] = Field(default=None, max_length=50)
    measurement_id: Optional[str] = Field(default=None, max_length=50)
    api_secret: Optional[str] = None
    custom_endpoint_path: Optional[str] = Field(default=None, max_length=100)
    custom_headers: Optional[dict[str, str]] = None
    is_active: Optional[bool] = None

    @field_validator("sgtm_url")
    @classmethod
    def validate_sgtm_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate sGTM URL format."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("sgtm_url must be a valid HTTP/HTTPS URL")
        return v.rstrip("/") if v else v

    @field_validator("custom_endpoint_path")
    @classmethod
    def validate_custom_endpoint_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate custom endpoint path format."""
        if v and not v.startswith("/"):
            return "/" + v
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "sgtm_url": "https://new-tags.upscript.com",
                "client_type": "custom",
                "custom_endpoint_path": "/events",
                "is_active": False,
            }
        }


class SgtmConfigResponse(BaseModel):
    """sGTM config response schema."""

    id: int
    storefront_id: int
    sgtm_url: str
    client_type: SgtmClientType
    container_id: Optional[str]
    measurement_id: Optional[str]
    custom_endpoint_path: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Note: api_secret and custom_headers are not returned for security

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "storefront_id": 1,
                "sgtm_url": "https://tags.upscript.com",
                "client_type": "ga4",
                "container_id": "GTM-XXXXXX",
                "measurement_id": "G-XXXXXX",
                "custom_endpoint_path": "/collect",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }


class SgtmConfigWithSecretsResponse(SgtmConfigResponse):
    """sGTM config response with secrets (for admin use with ?decrypt=true)."""

    api_secret: Optional[str] = None
    custom_headers: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True
