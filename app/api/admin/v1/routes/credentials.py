"""Credential admin CRUD endpoints with encryption."""

from typing import Optional, Union

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_credential_service, require_auth
from app.schemas.common import PaginatedResponse
from app.schemas.credential import (
    CredentialCreate,
    CredentialResponse,
    CredentialUpdate,
    CredentialWithSecretsResponse,
)
from app.services.credential_service import CredentialService

router = APIRouter(prefix="/credentials", tags=["Admin - Credentials"])


@router.get(
    "",
    response_model=PaginatedResponse[CredentialResponse],
    summary="List credentials",
    description="Get a paginated list of platform credentials (secrets not included)",
)
async def list_credentials(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    storefront_id: Optional[int] = Query(default=None),
    platform_id: Optional[int] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    _: str = Depends(require_auth),
    service: CredentialService = Depends(get_credential_service),
) -> PaginatedResponse[CredentialResponse]:
    """List all credentials with pagination and filters."""
    credentials, total = await service.get_all(
        skip=skip,
        limit=limit,
        storefront_id=storefront_id,
        platform_id=platform_id,
        is_active=is_active,
    )

    items = [CredentialResponse.model_validate(c) for c in credentials]
    return PaginatedResponse.create(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/{credential_id}",
    response_model=Union[CredentialResponse, CredentialWithSecretsResponse],
    summary="Get credential",
    description="Get a credential by ID. Use ?decrypt=true to include decrypted secrets.",
    responses={404: {"description": "Credential not found"}},
)
async def get_credential(
    credential_id: int,
    decrypt: bool = Query(default=False, description="Include decrypted credentials"),
    _: str = Depends(require_auth),
    service: CredentialService = Depends(get_credential_service),
) -> Union[CredentialResponse, CredentialWithSecretsResponse]:
    """
    Get a specific credential by ID.

    - Without `?decrypt=true`: Returns metadata only (no secrets)
    - With `?decrypt=true`: Returns metadata plus decrypted credentials
    """
    credential, decrypted = await service.get_by_id(credential_id, decrypt=decrypt)

    # Build response with optional platform/storefront info
    response_data = {
        "id": credential.id,
        "storefront_id": credential.storefront_id,
        "platform_id": credential.platform_id,
        "destination_type": credential.destination_type,
        "pixel_id": credential.pixel_id,
        "account_id": credential.account_id,
        "is_active": credential.is_active,
        "last_used_at": credential.last_used_at,
        "last_error": credential.last_error,
        "created_at": credential.created_at,
        "updated_at": credential.updated_at,
    }

    # Add related info if loaded
    if credential.platform:
        response_data["platform_code"] = credential.platform.platform_code
        response_data["platform_name"] = credential.platform.name
    if credential.storefront:
        response_data["storefront_name"] = credential.storefront.name

    if decrypt and decrypted:
        response_data["credentials"] = decrypted
        return CredentialWithSecretsResponse(**response_data)

    return CredentialResponse(**response_data)


@router.post(
    "",
    response_model=CredentialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create credential",
    description="Create a new platform credential (credentials are encrypted before storage)",
    responses={
        404: {"description": "Storefront or Platform not found"},
        409: {"description": "Credential already exists for storefront/platform"},
    },
)
async def create_credential(
    data: CredentialCreate,
    _: str = Depends(require_auth),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialResponse:
    """Create a new credential with encrypted storage."""
    credential = await service.create(data)
    return CredentialResponse.model_validate(credential)


@router.put(
    "/{credential_id}",
    response_model=CredentialResponse,
    summary="Update credential",
    description="Update an existing credential (new credentials are encrypted)",
    responses={404: {"description": "Credential not found"}},
)
async def update_credential(
    credential_id: int,
    data: CredentialUpdate,
    _: str = Depends(require_auth),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialResponse:
    """Update an existing credential."""
    credential = await service.update(credential_id, data)
    return CredentialResponse.model_validate(credential)


@router.delete(
    "/{credential_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete credential",
    description="Delete a platform credential",
    responses={404: {"description": "Credential not found"}},
)
async def delete_credential(
    credential_id: int,
    _: str = Depends(require_auth),
    service: CredentialService = Depends(get_credential_service),
) -> None:
    """Delete a credential."""
    await service.delete(credential_id)
