"""Health check endpoints."""

from fastapi import APIRouter, status

from app.core.config import settings
from app.core.database import check_database_connection
from app.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Check if the service is alive",
)
async def health() -> HealthResponse:
    """Liveness probe - always returns healthy if app is running."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Check if the service is ready to accept requests",
    responses={
        503: {"description": "Service not ready"},
    },
)
async def readiness() -> ReadinessResponse:
    """Readiness probe - checks database connectivity."""
    db_healthy = await check_database_connection()

    if not db_healthy:
        return ReadinessResponse(
            status="not_ready",
            database="unhealthy",
        )

    return ReadinessResponse(
        status="ready",
        database="healthy",
    )
