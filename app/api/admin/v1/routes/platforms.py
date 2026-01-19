"""Platform admin CRUD endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_platform_service, require_auth
from app.schemas.common import PaginatedResponse
from app.schemas.platform import PlatformCreate, PlatformResponse, PlatformUpdate
from app.services.platform_service import PlatformService

router = APIRouter(prefix="/platforms", tags=["Admin - Platforms"])


@router.get(
    "",
    response_model=PaginatedResponse[PlatformResponse],
    summary="List platforms",
    description="Get a paginated list of ad analytics platforms",
)
async def list_platforms(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    is_active: Optional[bool] = Query(default=None),
    tier: Optional[int] = Query(default=None, ge=1, le=3),
    category: Optional[str] = Query(default=None),
    _: str = Depends(require_auth),
    service: PlatformService = Depends(get_platform_service),
) -> PaginatedResponse[PlatformResponse]:
    """List all platforms with pagination and filters."""
    platforms, total = await service.get_all(
        skip=skip,
        limit=limit,
        is_active=is_active,
        tier=tier,
        category=category,
    )

    items = [PlatformResponse.model_validate(p) for p in platforms]
    return PaginatedResponse.create(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/{platform_id}",
    response_model=PlatformResponse,
    summary="Get platform",
    description="Get a platform by ID",
    responses={404: {"description": "Platform not found"}},
)
async def get_platform(
    platform_id: int,
    _: str = Depends(require_auth),
    service: PlatformService = Depends(get_platform_service),
) -> PlatformResponse:
    """Get a specific platform by ID."""
    platform = await service.get_by_id(platform_id)
    return PlatformResponse.model_validate(platform)


@router.post(
    "",
    response_model=PlatformResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create platform",
    description="Create a new ad analytics platform",
    responses={409: {"description": "Platform code already exists"}},
)
async def create_platform(
    data: PlatformCreate,
    _: str = Depends(require_auth),
    service: PlatformService = Depends(get_platform_service),
) -> PlatformResponse:
    """Create a new platform."""
    platform = await service.create(data)
    return PlatformResponse.model_validate(platform)


@router.put(
    "/{platform_id}",
    response_model=PlatformResponse,
    summary="Update platform",
    description="Update an existing platform",
    responses={404: {"description": "Platform not found"}},
)
async def update_platform(
    platform_id: int,
    data: PlatformUpdate,
    _: str = Depends(require_auth),
    service: PlatformService = Depends(get_platform_service),
) -> PlatformResponse:
    """Update an existing platform."""
    platform = await service.update(platform_id, data)
    return PlatformResponse.model_validate(platform)


@router.delete(
    "/{platform_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete platform",
    description="Delete a platform and all associated credentials",
    responses={404: {"description": "Platform not found"}},
)
async def delete_platform(
    platform_id: int,
    _: str = Depends(require_auth),
    service: PlatformService = Depends(get_platform_service),
) -> None:
    """Delete a platform."""
    await service.delete(platform_id)
