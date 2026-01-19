"""sGTM Config service for business logic."""

from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import get_encryption
from app.models.sgtm_config import StorefrontSgtmConfig
from app.repositories.sgtm_config_repository import SgtmConfigRepository
from app.repositories.storefront_repository import StorefrontRepository
from app.schemas.sgtm_config import SgtmConfigCreate, SgtmConfigUpdate


class SgtmConfigService:
    """Service for sGTM config operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = SgtmConfigRepository(session)
        self.storefront_repo = StorefrontRepository(session)
        self.encryption = get_encryption()

    async def get_by_id(self, id: int) -> StorefrontSgtmConfig:
        """Get sGTM config by ID."""
        config = await self.repository.get_by_id(id)
        if not config:
            raise NotFoundError("SgtmConfig", id)
        return config

    async def get_by_storefront_id(self, storefront_id: int) -> StorefrontSgtmConfig:
        """Get sGTM config by storefront ID."""
        config = await self.repository.get_by_storefront_id(storefront_id)
        if not config:
            raise NotFoundError("SgtmConfig", f"storefront_id={storefront_id}")
        return config

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> tuple[Sequence[StorefrontSgtmConfig], int]:
        """Get all sGTM configs with pagination."""
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active

        configs = await self.repository.get_all(skip=skip, limit=limit, filters=filters)
        total = await self.repository.count(filters=filters)
        return configs, total

    async def create(self, data: SgtmConfigCreate) -> StorefrontSgtmConfig:
        """Create a new sGTM config."""
        # Verify storefront exists
        storefront = await self.storefront_repo.get_by_id(data.storefront_id)
        if not storefront:
            raise NotFoundError("Storefront", data.storefront_id)

        # Check for duplicate config
        if await self.repository.config_exists_for_storefront(data.storefront_id):
            raise ConflictError(
                f"sGTM config already exists for storefront {data.storefront_id}",
                details={"storefront_id": data.storefront_id},
            )

        # Encrypt api_secret if provided
        create_data = data.model_dump()
        if create_data.get("api_secret"):
            create_data["api_secret"] = self.encryption.encrypt(
                {"api_secret": create_data["api_secret"]}
            )

        return await self.repository.create(create_data)

    async def update(self, id: int, data: SgtmConfigUpdate) -> StorefrontSgtmConfig:
        """Update an sGTM config."""
        config = await self.get_by_id(id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return config

        # Encrypt api_secret if being updated
        if "api_secret" in update_data and update_data["api_secret"]:
            update_data["api_secret"] = self.encryption.encrypt(
                {"api_secret": update_data["api_secret"]}
            )

        return await self.repository.update(config, update_data)

    async def delete(self, id: int) -> bool:
        """Delete an sGTM config."""
        config = await self.get_by_id(id)
        return await self.repository.delete(config)

    async def get_decrypted_secret(self, id: int) -> Optional[str]:
        """Get decrypted API secret."""
        config = await self.get_by_id(id)
        if not config.api_secret:
            return None

        decrypted = self.encryption.decrypt(config.api_secret)
        return decrypted.get("api_secret")
