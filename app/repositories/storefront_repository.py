"""Storefront repository."""

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.storefront import Storefront
from app.repositories.base import BaseRepository


class StorefrontRepository(BaseRepository[Storefront]):
    """Repository for Storefront entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(Storefront, session)

    async def get_by_storefront_id(self, storefront_id: str) -> Optional[Storefront]:
        """Get storefront by external storefront_id."""
        result = await self.session.execute(
            select(Storefront).where(Storefront.storefront_id == storefront_id)
        )
        return result.scalar_one_or_none()

    async def get_with_config(self, id: int) -> Optional[Storefront]:
        """Get storefront with sGTM config loaded."""
        result = await self.session.execute(
            select(Storefront)
            .options(selectinload(Storefront.sgtm_config))
            .where(Storefront.id == id)
        )
        return result.scalar_one_or_none()

    async def get_with_credentials(self, id: int) -> Optional[Storefront]:
        """Get storefront with credentials loaded."""
        result = await self.session.execute(
            select(Storefront)
            .options(selectinload(Storefront.credentials))
            .where(Storefront.id == id)
        )
        return result.scalar_one_or_none()

    async def get_active_storefronts(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Storefront]:
        """Get all active storefronts."""
        result = await self.session.execute(
            select(Storefront)
            .where(Storefront.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def storefront_id_exists(self, storefront_id: str) -> bool:
        """Check if external storefront_id already exists."""
        existing = await self.get_by_storefront_id(storefront_id)
        return existing is not None
