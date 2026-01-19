"""Platform repository."""

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import AdAnalyticsPlatform
from app.repositories.base import BaseRepository


class PlatformRepository(BaseRepository[AdAnalyticsPlatform]):
    """Repository for AdAnalyticsPlatform entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(AdAnalyticsPlatform, session)

    async def get_by_platform_code(
        self, platform_code: str
    ) -> Optional[AdAnalyticsPlatform]:
        """Get platform by unique platform code."""
        result = await self.session.execute(
            select(AdAnalyticsPlatform).where(
                AdAnalyticsPlatform.platform_code == platform_code
            )
        )
        return result.scalar_one_or_none()

    async def get_by_tier(
        self,
        tier: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AdAnalyticsPlatform]:
        """Get platforms by tier."""
        result = await self.session.execute(
            select(AdAnalyticsPlatform)
            .where(AdAnalyticsPlatform.tier == tier)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AdAnalyticsPlatform]:
        """Get platforms by category."""
        result = await self.session.execute(
            select(AdAnalyticsPlatform)
            .where(AdAnalyticsPlatform.category == category)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_platforms(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AdAnalyticsPlatform]:
        """Get all active platforms ordered by tier."""
        result = await self.session.execute(
            select(AdAnalyticsPlatform)
            .where(AdAnalyticsPlatform.is_active == True)
            .order_by(AdAnalyticsPlatform.tier, AdAnalyticsPlatform.name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def platform_code_exists(self, platform_code: str) -> bool:
        """Check if platform code already exists."""
        existing = await self.get_by_platform_code(platform_code)
        return existing is not None
