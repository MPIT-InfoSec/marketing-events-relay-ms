"""Storefront service for business logic."""

from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.storefront import Storefront
from app.repositories.storefront_repository import StorefrontRepository
from app.schemas.storefront import StorefrontCreate, StorefrontUpdate


class StorefrontService:
    """Service for storefront operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = StorefrontRepository(session)

    async def get_by_id(self, id: int) -> Storefront:
        """Get storefront by ID."""
        storefront = await self.repository.get_by_id(id)
        if not storefront:
            raise NotFoundError("Storefront", id)
        return storefront

    async def get_by_storefront_id(self, storefront_id: str) -> Storefront:
        """Get storefront by external storefront_id."""
        storefront = await self.repository.get_by_storefront_id(storefront_id)
        if not storefront:
            raise NotFoundError("Storefront", storefront_id)
        return storefront

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> tuple[Sequence[Storefront], int]:
        """Get all storefronts with pagination."""
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active

        storefronts = await self.repository.get_all(skip=skip, limit=limit, filters=filters)
        total = await self.repository.count(filters=filters)
        return storefronts, total

    async def create(self, data: StorefrontCreate) -> Storefront:
        """Create a new storefront."""
        # Check for duplicate storefront_id
        if await self.repository.storefront_id_exists(data.storefront_id):
            raise ConflictError(
                f"Storefront with storefront_id '{data.storefront_id}' already exists",
                details={"storefront_id": data.storefront_id},
            )

        return await self.repository.create(data.model_dump())

    async def update(self, id: int, data: StorefrontUpdate) -> Storefront:
        """Update a storefront."""
        storefront = await self.get_by_id(id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return storefront

        return await self.repository.update(storefront, update_data)

    async def delete(self, id: int) -> bool:
        """Delete a storefront."""
        storefront = await self.get_by_id(id)
        return await self.repository.delete(storefront)

    async def get_with_config(self, id: int) -> Storefront:
        """Get storefront with sGTM config."""
        storefront = await self.repository.get_with_config(id)
        if not storefront:
            raise NotFoundError("Storefront", id)
        return storefront

    async def get_with_credentials(self, id: int) -> Storefront:
        """Get storefront with credentials."""
        storefront = await self.repository.get_with_credentials(id)
        if not storefront:
            raise NotFoundError("Storefront", id)
        return storefront
