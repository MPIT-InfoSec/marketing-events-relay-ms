"""Credential service for business logic with encryption."""

from typing import Any, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import get_encryption
from app.models.credential import PlatformCredential
from app.repositories.credential_repository import CredentialRepository
from app.repositories.platform_repository import PlatformRepository
from app.repositories.storefront_repository import StorefrontRepository
from app.schemas.credential import CredentialCreate, CredentialUpdate


class CredentialService:
    """Service for credential operations with encryption."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CredentialRepository(session)
        self.storefront_repo = StorefrontRepository(session)
        self.platform_repo = PlatformRepository(session)
        self.encryption = get_encryption()

    async def get_by_id(
        self,
        id: int,
        decrypt: bool = False,
    ) -> tuple[PlatformCredential, Optional[dict[str, Any]]]:
        """
        Get credential by ID.

        Returns:
            Tuple of (credential, decrypted_credentials or None)
        """
        credential = await self.repository.get_with_relations(id)
        if not credential:
            raise NotFoundError("Credential", id)

        decrypted = None
        if decrypt:
            decrypted = self.encryption.decrypt(credential.credentials_encrypted)

        return credential, decrypted

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        storefront_id: Optional[int] = None,
        platform_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[Sequence[PlatformCredential], int]:
        """Get all credentials with pagination and filters."""
        filters = {}
        if storefront_id is not None:
            filters["storefront_id"] = storefront_id
        if platform_id is not None:
            filters["platform_id"] = platform_id
        if is_active is not None:
            filters["is_active"] = is_active

        credentials = await self.repository.get_all(skip=skip, limit=limit, filters=filters)
        total = await self.repository.count(filters=filters)
        return credentials, total

    async def create(self, data: CredentialCreate) -> PlatformCredential:
        """Create a new credential with encrypted storage."""
        # Verify storefront exists
        storefront = await self.storefront_repo.get_by_id(data.storefront_id)
        if not storefront:
            raise NotFoundError("Storefront", data.storefront_id)

        # Verify platform exists
        platform = await self.platform_repo.get_by_id(data.platform_id)
        if not platform:
            raise NotFoundError("Platform", data.platform_id)

        # Check for duplicate credential
        if await self.repository.credential_exists(data.storefront_id, data.platform_id):
            raise ConflictError(
                f"Credential already exists for storefront {data.storefront_id} and platform {data.platform_id}",
                details={
                    "storefront_id": data.storefront_id,
                    "platform_id": data.platform_id,
                },
            )

        # Encrypt credentials
        create_data = data.model_dump(exclude={"credentials"})
        create_data["credentials_encrypted"] = self.encryption.encrypt(data.credentials)

        return await self.repository.create(create_data)

    async def update(self, id: int, data: CredentialUpdate) -> PlatformCredential:
        """Update a credential."""
        credential, _ = await self.get_by_id(id)

        update_data = data.model_dump(exclude_unset=True, exclude={"credentials"})

        # Encrypt new credentials if provided
        if data.credentials is not None:
            update_data["credentials_encrypted"] = self.encryption.encrypt(data.credentials)

        if not update_data:
            return credential

        return await self.repository.update(credential, update_data)

    async def delete(self, id: int) -> bool:
        """Delete a credential."""
        credential, _ = await self.get_by_id(id)
        return await self.repository.delete(credential)

    async def get_by_storefront(
        self,
        storefront_id: int,
        active_only: bool = True,
    ) -> Sequence[PlatformCredential]:
        """Get all credentials for a storefront."""
        return await self.repository.get_by_storefront(
            storefront_id,
            active_only=active_only,
        )

    async def get_active_for_event(
        self,
        storefront_id: int,
    ) -> Sequence[PlatformCredential]:
        """Get active credentials for event processing."""
        return await self.repository.get_active_credentials_for_event(storefront_id)

    async def mark_used(
        self,
        id: int,
        error: Optional[str] = None,
    ) -> None:
        """Mark credential as used and optionally record error."""
        await self.repository.update_last_used(id, error=error)
