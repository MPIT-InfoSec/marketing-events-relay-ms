"""API dependencies for dependency injection."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_basic_auth
from app.services.credential_service import CredentialService
from app.services.event_service import EventService
from app.services.forwarding_service import ForwardingService
from app.services.platform_service import PlatformService
from app.services.sgtm_config_service import SgtmConfigService
from app.services.storefront_service import StorefrontService


# Database session dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async for session in get_db():
        yield session


# Service dependencies
async def get_storefront_service(
    session: AsyncSession = Depends(get_session),
) -> StorefrontService:
    """Get storefront service instance."""
    return StorefrontService(session)


async def get_sgtm_config_service(
    session: AsyncSession = Depends(get_session),
) -> SgtmConfigService:
    """Get sGTM config service instance."""
    return SgtmConfigService(session)


async def get_platform_service(
    session: AsyncSession = Depends(get_session),
) -> PlatformService:
    """Get platform service instance."""
    return PlatformService(session)


async def get_credential_service(
    session: AsyncSession = Depends(get_session),
) -> CredentialService:
    """Get credential service instance."""
    return CredentialService(session)


async def get_event_service(
    session: AsyncSession = Depends(get_session),
) -> EventService:
    """Get event service instance."""
    return EventService(session)


async def get_forwarding_service(
    session: AsyncSession = Depends(get_session),
) -> ForwardingService:
    """Get forwarding service instance."""
    return ForwardingService(session)


# Auth dependency for protected routes
def require_auth(username: str = Depends(verify_basic_auth)) -> str:
    """Require authentication."""
    return username
