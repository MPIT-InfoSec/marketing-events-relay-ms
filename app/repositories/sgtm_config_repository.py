"""sGTM Config repository."""

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sgtm_config import StorefrontSgtmConfig
from app.repositories.base import BaseRepository


class SgtmConfigRepository(BaseRepository[StorefrontSgtmConfig]):
    """Repository for StorefrontSgtmConfig entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(StorefrontSgtmConfig, session)

    async def get_by_storefront_id(
        self, storefront_id: int
    ) -> Optional[StorefrontSgtmConfig]:
        """Get sGTM config by storefront ID."""
        result = await self.session.execute(
            select(StorefrontSgtmConfig).where(
                StorefrontSgtmConfig.storefront_id == storefront_id
            )
        )
        return result.scalar_one_or_none()

    async def get_with_storefront(self, id: int) -> Optional[StorefrontSgtmConfig]:
        """Get sGTM config with storefront loaded."""
        result = await self.session.execute(
            select(StorefrontSgtmConfig)
            .options(selectinload(StorefrontSgtmConfig.storefront))
            .where(StorefrontSgtmConfig.id == id)
        )
        return result.scalar_one_or_none()

    async def get_active_configs(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[StorefrontSgtmConfig]:
        """Get all active sGTM configs."""
        result = await self.session.execute(
            select(StorefrontSgtmConfig)
            .options(selectinload(StorefrontSgtmConfig.storefront))
            .where(StorefrontSgtmConfig.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def config_exists_for_storefront(self, storefront_id: int) -> bool:
        """Check if config already exists for storefront."""
        existing = await self.get_by_storefront_id(storefront_id)
        return existing is not None
