"""Platform service for business logic."""

from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.platform import AdAnalyticsPlatform
from app.repositories.platform_repository import PlatformRepository
from app.schemas.platform import PlatformCreate, PlatformUpdate


class PlatformService:
    """Service for platform operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = PlatformRepository(session)

    async def get_by_id(self, id: int) -> AdAnalyticsPlatform:
        """Get platform by ID."""
        platform = await self.repository.get_by_id(id)
        if not platform:
            raise NotFoundError("Platform", id)
        return platform

    async def get_by_platform_code(self, platform_code: str) -> AdAnalyticsPlatform:
        """Get platform by code."""
        platform = await self.repository.get_by_platform_code(platform_code)
        if not platform:
            raise NotFoundError("Platform", platform_code)
        return platform

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        tier: Optional[int] = None,
        category: Optional[str] = None,
    ) -> tuple[Sequence[AdAnalyticsPlatform], int]:
        """Get all platforms with pagination and filters."""
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        if tier is not None:
            filters["tier"] = tier
        if category is not None:
            filters["category"] = category

        platforms = await self.repository.get_all(skip=skip, limit=limit, filters=filters)
        total = await self.repository.count(filters=filters)
        return platforms, total

    async def create(self, data: PlatformCreate) -> AdAnalyticsPlatform:
        """Create a new platform."""
        # Check for duplicate platform_code
        if await self.repository.platform_code_exists(data.platform_code):
            raise ConflictError(
                f"Platform with code '{data.platform_code}' already exists",
                details={"platform_code": data.platform_code},
            )

        return await self.repository.create(data.model_dump())

    async def update(self, id: int, data: PlatformUpdate) -> AdAnalyticsPlatform:
        """Update a platform."""
        platform = await self.get_by_id(id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return platform

        return await self.repository.update(platform, update_data)

    async def delete(self, id: int) -> bool:
        """Delete a platform."""
        platform = await self.get_by_id(id)
        return await self.repository.delete(platform)

    async def get_by_tier(
        self,
        tier: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AdAnalyticsPlatform]:
        """Get platforms by tier."""
        return await self.repository.get_by_tier(tier, skip=skip, limit=limit)

    async def get_active_platforms(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AdAnalyticsPlatform]:
        """Get all active platforms ordered by tier."""
        return await self.repository.get_active_platforms(skip=skip, limit=limit)
