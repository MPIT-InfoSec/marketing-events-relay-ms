"""Storefront admin CRUD endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_storefront_service, require_auth
from app.schemas.common import PaginatedResponse
from app.schemas.storefront import StorefrontCreate, StorefrontResponse, StorefrontUpdate
from app.services.storefront_service import StorefrontService

router = APIRouter(prefix="/storefronts", tags=["Admin - Storefronts"])


@router.get(
    "",
    response_model=PaginatedResponse[StorefrontResponse],
    summary="List storefronts",
    description="Get a paginated list of storefronts",
)
async def list_storefronts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    is_active: Optional[bool] = Query(default=None),
    _: str = Depends(require_auth),
    service: StorefrontService = Depends(get_storefront_service),
) -> PaginatedResponse[StorefrontResponse]:
    """List all storefronts with pagination."""
    storefronts, total = await service.get_all(
        skip=skip,
        limit=limit,
        is_active=is_active,
    )

    items = [StorefrontResponse.model_validate(s) for s in storefronts]
    return PaginatedResponse.create(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/{storefront_id}",
    response_model=StorefrontResponse,
    summary="Get storefront",
    description="Get a storefront by ID",
    responses={404: {"description": "Storefront not found"}},
)
async def get_storefront(
    storefront_id: int,
    _: str = Depends(require_auth),
    service: StorefrontService = Depends(get_storefront_service),
) -> StorefrontResponse:
    """Get a specific storefront by ID."""
    storefront = await service.get_by_id(storefront_id)
    return StorefrontResponse.model_validate(storefront)


@router.post(
    "",
    response_model=StorefrontResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create storefront",
    description="Create a new storefront",
    responses={409: {"description": "Storefront ID already exists"}},
)
async def create_storefront(
    data: StorefrontCreate,
    _: str = Depends(require_auth),
    service: StorefrontService = Depends(get_storefront_service),
) -> StorefrontResponse:
    """Create a new storefront."""
    storefront = await service.create(data)
    return StorefrontResponse.model_validate(storefront)


@router.put(
    "/{storefront_id}",
    response_model=StorefrontResponse,
    summary="Update storefront",
    description="Update an existing storefront",
    responses={404: {"description": "Storefront not found"}},
)
async def update_storefront(
    storefront_id: int,
    data: StorefrontUpdate,
    _: str = Depends(require_auth),
    service: StorefrontService = Depends(get_storefront_service),
) -> StorefrontResponse:
    """Update an existing storefront."""
    storefront = await service.update(storefront_id, data)
    return StorefrontResponse.model_validate(storefront)


@router.delete(
    "/{storefront_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete storefront",
    description="Delete a storefront and all associated data",
    responses={404: {"description": "Storefront not found"}},
)
async def delete_storefront(
    storefront_id: int,
    _: str = Depends(require_auth),
    service: StorefrontService = Depends(get_storefront_service),
) -> None:
    """Delete a storefront."""
    await service.delete(storefront_id)
