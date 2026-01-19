"""sGTM Config admin CRUD endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_sgtm_config_service, require_auth
from app.schemas.common import PaginatedResponse
from app.schemas.sgtm_config import SgtmConfigCreate, SgtmConfigResponse, SgtmConfigUpdate
from app.services.sgtm_config_service import SgtmConfigService

router = APIRouter(prefix="/sgtm-configs", tags=["Admin - sGTM Configs"])


@router.get(
    "",
    response_model=PaginatedResponse[SgtmConfigResponse],
    summary="List sGTM configs",
    description="Get a paginated list of sGTM configurations",
)
async def list_sgtm_configs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    is_active: Optional[bool] = Query(default=None),
    _: str = Depends(require_auth),
    service: SgtmConfigService = Depends(get_sgtm_config_service),
) -> PaginatedResponse[SgtmConfigResponse]:
    """List all sGTM configs with pagination."""
    configs, total = await service.get_all(
        skip=skip,
        limit=limit,
        is_active=is_active,
    )

    items = [SgtmConfigResponse.model_validate(c) for c in configs]
    return PaginatedResponse.create(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/{config_id}",
    response_model=SgtmConfigResponse,
    summary="Get sGTM config",
    description="Get an sGTM configuration by ID",
    responses={404: {"description": "Config not found"}},
)
async def get_sgtm_config(
    config_id: int,
    _: str = Depends(require_auth),
    service: SgtmConfigService = Depends(get_sgtm_config_service),
) -> SgtmConfigResponse:
    """Get a specific sGTM config by ID."""
    config = await service.get_by_id(config_id)
    return SgtmConfigResponse.model_validate(config)


@router.post(
    "",
    response_model=SgtmConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create sGTM config",
    description="Create a new sGTM configuration for a storefront",
    responses={
        404: {"description": "Storefront not found"},
        409: {"description": "Config already exists for storefront"},
    },
)
async def create_sgtm_config(
    data: SgtmConfigCreate,
    _: str = Depends(require_auth),
    service: SgtmConfigService = Depends(get_sgtm_config_service),
) -> SgtmConfigResponse:
    """Create a new sGTM config."""
    config = await service.create(data)
    return SgtmConfigResponse.model_validate(config)


@router.put(
    "/{config_id}",
    response_model=SgtmConfigResponse,
    summary="Update sGTM config",
    description="Update an existing sGTM configuration",
    responses={404: {"description": "Config not found"}},
)
async def update_sgtm_config(
    config_id: int,
    data: SgtmConfigUpdate,
    _: str = Depends(require_auth),
    service: SgtmConfigService = Depends(get_sgtm_config_service),
) -> SgtmConfigResponse:
    """Update an existing sGTM config."""
    config = await service.update(config_id, data)
    return SgtmConfigResponse.model_validate(config)


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete sGTM config",
    description="Delete an sGTM configuration",
    responses={404: {"description": "Config not found"}},
)
async def delete_sgtm_config(
    config_id: int,
    _: str = Depends(require_auth),
    service: SgtmConfigService = Depends(get_sgtm_config_service),
) -> None:
    """Delete an sGTM config."""
    await service.delete(config_id)
