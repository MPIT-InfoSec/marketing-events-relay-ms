"""Pydantic schemas for request/response validation."""

from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationParams
from app.schemas.credential import (
    CredentialCreate,
    CredentialResponse,
    CredentialUpdate,
    CredentialWithSecretsResponse,
)
from app.schemas.event import (
    EventBatchRequest,
    EventBatchResponse,
    EventCreate,
    EventDataItem,
    EventResponse,
    EventWithAttemptsResponse,
)
from app.schemas.platform import PlatformCreate, PlatformResponse, PlatformUpdate
from app.schemas.sgtm_config import SgtmConfigCreate, SgtmConfigResponse, SgtmConfigUpdate
from app.schemas.storefront import StorefrontCreate, StorefrontResponse, StorefrontUpdate

__all__ = [
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "StorefrontCreate",
    "StorefrontUpdate",
    "StorefrontResponse",
    "SgtmConfigCreate",
    "SgtmConfigUpdate",
    "SgtmConfigResponse",
    "PlatformCreate",
    "PlatformUpdate",
    "PlatformResponse",
    "CredentialCreate",
    "CredentialUpdate",
    "CredentialResponse",
    "CredentialWithSecretsResponse",
    "EventCreate",
    "EventDataItem",
    "EventBatchRequest",
    "EventBatchResponse",
    "EventResponse",
    "EventWithAttemptsResponse",
]
