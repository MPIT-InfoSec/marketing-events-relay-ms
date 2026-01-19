"""Credential repository."""

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.credential import PlatformCredential
from app.repositories.base import BaseRepository


class CredentialRepository(BaseRepository[PlatformCredential]):
    """Repository for PlatformCredential entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(PlatformCredential, session)

    async def get_by_storefront_and_platform(
        self,
        storefront_id: int,
        platform_id: int,
    ) -> Optional[PlatformCredential]:
        """Get credential by storefront and platform combination."""
        result = await self.session.execute(
            select(PlatformCredential).where(
                PlatformCredential.storefront_id == storefront_id,
                PlatformCredential.platform_id == platform_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_with_relations(self, id: int) -> Optional[PlatformCredential]:
        """Get credential with storefront and platform loaded."""
        result = await self.session.execute(
            select(PlatformCredential)
            .options(
                selectinload(PlatformCredential.storefront),
                selectinload(PlatformCredential.platform),
            )
            .where(PlatformCredential.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_storefront(
        self,
        storefront_id: int,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[PlatformCredential]:
        """Get all credentials for a storefront."""
        query = (
            select(PlatformCredential)
            .options(selectinload(PlatformCredential.platform))
            .where(PlatformCredential.storefront_id == storefront_id)
        )

        if active_only:
            query = query.where(PlatformCredential.is_active == True)

        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def get_active_credentials_for_event(
        self,
        storefront_id: int,
    ) -> Sequence[PlatformCredential]:
        """Get active credentials for event processing (with active platforms)."""
        result = await self.session.execute(
            select(PlatformCredential)
            .options(
                selectinload(PlatformCredential.platform),
                selectinload(PlatformCredential.storefront),
            )
            .join(PlatformCredential.platform)
            .join(PlatformCredential.storefront)
            .where(
                PlatformCredential.storefront_id == storefront_id,
                PlatformCredential.is_active == True,
                PlatformCredential.platform.has(is_active=True),
                PlatformCredential.storefront.has(is_active=True),
            )
        )
        return result.scalars().all()

    async def update_last_used(
        self,
        id: int,
        error: Optional[str] = None,
    ) -> None:
        """Update last_used_at and optionally set last_error."""
        values = {"last_used_at": datetime.utcnow()}
        if error:
            values["last_error"] = error
        else:
            values["last_error"] = None

        await self.session.execute(
            update(PlatformCredential)
            .where(PlatformCredential.id == id)
            .values(**values)
        )
        await self.session.flush()

    async def credential_exists(
        self,
        storefront_id: int,
        platform_id: int,
    ) -> bool:
        """Check if credential already exists for storefront/platform."""
        existing = await self.get_by_storefront_and_platform(storefront_id, platform_id)
        return existing is not None
