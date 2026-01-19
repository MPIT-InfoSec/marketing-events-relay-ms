"""Unit tests for service layer business logic."""

import json
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ConflictError, KillSwitchError, NotFoundError, ValidationError
from app.models.enums import (
    AttemptStatus,
    DestinationType,
    EventStatus,
    SgtmClientType,
)
from app.models.credential import PlatformCredential
from app.models.event import MarketingEvent
from app.models.platform import AdAnalyticsPlatform
from app.models.sgtm_config import StorefrontSgtmConfig
from app.models.storefront import Storefront
from app.schemas.credential import CredentialCreate, CredentialUpdate
from app.schemas.event import EventBatchRequest, EventDataItem
from app.schemas.platform import PlatformCreate, PlatformUpdate
from app.schemas.sgtm_config import SgtmConfigCreate, SgtmConfigUpdate
from app.schemas.storefront import StorefrontCreate, StorefrontUpdate
from app.services.credential_service import CredentialService
from app.services.event_service import EventService
from app.services.forwarding_service import ForwardingService
from app.services.platform_service import PlatformService
from app.services.sgtm_config_service import SgtmConfigService
from app.services.storefront_service import StorefrontService


# ============================================================================
# StorefrontService Tests
# ============================================================================


class TestStorefrontService:
    """Tests for StorefrontService."""

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        return AsyncMock()

    @pytest.fixture
    def mock_storefront(self):
        """Create mock storefront."""
        storefront = MagicMock(spec=Storefront)
        storefront.id = 1
        storefront.storefront_id = "test-store"
        storefront.name = "Test Store"
        storefront.is_active = True
        return storefront

    @pytest.fixture
    def service(self, mock_session):
        """Create service with mocked repository."""
        service = StorefrontService(mock_session)
        service.repository = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, service, mock_storefront):
        """Test successful retrieval by ID."""
        service.repository.get_by_id.return_value = mock_storefront

        result = await service.get_by_id(1)

        assert result == mock_storefront
        service.repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service):
        """Test NotFoundError when storefront doesn't exist."""
        service.repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc:
            await service.get_by_id(999)

        assert "Storefront" in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_by_storefront_id_success(self, service, mock_storefront):
        """Test successful retrieval by storefront_id."""
        service.repository.get_by_storefront_id.return_value = mock_storefront

        result = await service.get_by_storefront_id("test-store")

        assert result == mock_storefront

    @pytest.mark.asyncio
    async def test_get_by_storefront_id_not_found(self, service):
        """Test NotFoundError when storefront_id doesn't exist."""
        service.repository.get_by_storefront_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_storefront_id("nonexistent")

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, service, mock_storefront):
        """Test getting all storefronts with pagination."""
        service.repository.get_all.return_value = [mock_storefront]
        service.repository.count.return_value = 1

        storefronts, total = await service.get_all(skip=0, limit=10)

        assert len(storefronts) == 1
        assert total == 1
        service.repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, service, mock_storefront):
        """Test getting storefronts with is_active filter."""
        service.repository.get_all.return_value = [mock_storefront]
        service.repository.count.return_value = 1

        storefronts, total = await service.get_all(is_active=True)

        service.repository.get_all.assert_called_once()
        call_kwargs = service.repository.get_all.call_args[1]
        assert call_kwargs["filters"] == {"is_active": True}

    @pytest.mark.asyncio
    async def test_create_success(self, service, mock_storefront):
        """Test successful storefront creation."""
        service.repository.storefront_id_exists.return_value = False
        service.repository.create.return_value = mock_storefront

        data = StorefrontCreate(
            storefront_id="new-store",
            name="New Store",
        )

        result = await service.create(data)

        assert result == mock_storefront
        service.repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_fails(self, service):
        """Test ConflictError when storefront_id already exists."""
        service.repository.storefront_id_exists.return_value = True

        data = StorefrontCreate(
            storefront_id="existing-store",
            name="Existing Store",
        )

        with pytest.raises(ConflictError) as exc:
            await service.create(data)

        assert "already exists" in str(exc.value)

    @pytest.mark.asyncio
    async def test_update_success(self, service, mock_storefront):
        """Test successful storefront update."""
        service.repository.get_by_id.return_value = mock_storefront
        updated_storefront = MagicMock(spec=Storefront)
        updated_storefront.name = "Updated Store"
        service.repository.update.return_value = updated_storefront

        data = StorefrontUpdate(name="Updated Store")

        result = await service.update(1, data)

        assert result.name == "Updated Store"
        service.repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_with_no_changes(self, service, mock_storefront):
        """Test update with no changes returns existing storefront."""
        service.repository.get_by_id.return_value = mock_storefront

        data = StorefrontUpdate()

        result = await service.update(1, data)

        assert result == mock_storefront
        service.repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_success(self, service, mock_storefront):
        """Test successful storefront deletion."""
        service.repository.get_by_id.return_value = mock_storefront
        service.repository.delete.return_value = True

        result = await service.delete(1)

        assert result is True
        service.repository.delete.assert_called_once_with(mock_storefront)

    @pytest.mark.asyncio
    async def test_delete_not_found(self, service):
        """Test deleting non-existent storefront."""
        service.repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.delete(999)

    @pytest.mark.asyncio
    async def test_get_with_config(self, service, mock_storefront):
        """Test getting storefront with sGTM config."""
        service.repository.get_with_config.return_value = mock_storefront

        result = await service.get_with_config(1)

        assert result == mock_storefront

    @pytest.mark.asyncio
    async def test_get_with_credentials(self, service, mock_storefront):
        """Test getting storefront with credentials."""
        service.repository.get_with_credentials.return_value = mock_storefront

        result = await service.get_with_credentials(1)

        assert result == mock_storefront


# ============================================================================
# PlatformService Tests
# ============================================================================


class TestPlatformService:
    """Tests for PlatformService."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def mock_platform(self):
        """Create mock platform."""
        platform = MagicMock(spec=AdAnalyticsPlatform)
        platform.id = 1
        platform.platform_code = "meta_capi"
        platform.name = "Meta CAPI"
        platform.tier = 1
        platform.category = "advertising"
        platform.is_active = True
        return platform

    @pytest.fixture
    def service(self, mock_session):
        service = PlatformService(mock_session)
        service.repository = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, service, mock_platform):
        """Test successful retrieval by ID."""
        service.repository.get_by_id.return_value = mock_platform

        result = await service.get_by_id(1)

        assert result == mock_platform

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service):
        """Test NotFoundError when platform doesn't exist."""
        service.repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_id(999)

    @pytest.mark.asyncio
    async def test_get_by_platform_code_success(self, service, mock_platform):
        """Test retrieval by platform code."""
        service.repository.get_by_platform_code.return_value = mock_platform

        result = await service.get_by_platform_code("meta_capi")

        assert result == mock_platform

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, service, mock_platform):
        """Test getting platforms with multiple filters."""
        service.repository.get_all.return_value = [mock_platform]
        service.repository.count.return_value = 1

        platforms, total = await service.get_all(
            tier=1,
            category="advertising",
            is_active=True,
        )

        call_kwargs = service.repository.get_all.call_args[1]
        assert call_kwargs["filters"]["tier"] == 1
        assert call_kwargs["filters"]["category"] == "advertising"
        assert call_kwargs["filters"]["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_success(self, service, mock_platform):
        """Test successful platform creation."""
        service.repository.platform_code_exists.return_value = False
        service.repository.create.return_value = mock_platform

        data = PlatformCreate(
            platform_code="new_platform",
            name="New Platform",
            category="analytics",
            tier=2,
        )

        result = await service.create(data)

        assert result == mock_platform

    @pytest.mark.asyncio
    async def test_create_duplicate_fails(self, service):
        """Test ConflictError when platform_code already exists."""
        service.repository.platform_code_exists.return_value = True

        data = PlatformCreate(
            platform_code="existing",
            name="Existing Platform",
            category="advertising",
            tier=1,
        )

        with pytest.raises(ConflictError):
            await service.create(data)

    @pytest.mark.asyncio
    async def test_update_success(self, service, mock_platform):
        """Test successful platform update."""
        service.repository.get_by_id.return_value = mock_platform
        updated = MagicMock()
        updated.tier = 2
        service.repository.update.return_value = updated

        data = PlatformUpdate(tier=2)

        result = await service.update(1, data)

        assert result.tier == 2

    @pytest.mark.asyncio
    async def test_delete_success(self, service, mock_platform):
        """Test successful platform deletion."""
        service.repository.get_by_id.return_value = mock_platform
        service.repository.delete.return_value = True

        result = await service.delete(1)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_by_tier(self, service, mock_platform):
        """Test getting platforms by tier."""
        service.repository.get_by_tier.return_value = [mock_platform]

        result = await service.get_by_tier(1)

        assert len(result) == 1
        service.repository.get_by_tier.assert_called_once_with(1, skip=0, limit=100)

    @pytest.mark.asyncio
    async def test_get_active_platforms(self, service, mock_platform):
        """Test getting active platforms."""
        service.repository.get_active_platforms.return_value = [mock_platform]

        result = await service.get_active_platforms()

        assert len(result) == 1


# ============================================================================
# CredentialService Tests
# ============================================================================


class TestCredentialService:
    """Tests for CredentialService."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def mock_credential(self):
        """Create mock credential."""
        credential = MagicMock(spec=PlatformCredential)
        credential.id = 1
        credential.storefront_id = 1
        credential.platform_id = 1
        credential.credentials_encrypted = "encrypted_data"
        credential.is_active = True
        return credential

    @pytest.fixture
    def mock_storefront(self):
        storefront = MagicMock(spec=Storefront)
        storefront.id = 1
        return storefront

    @pytest.fixture
    def mock_platform(self):
        platform = MagicMock(spec=AdAnalyticsPlatform)
        platform.id = 1
        return platform

    @pytest.fixture
    def service(self, mock_session):
        service = CredentialService(mock_session)
        service.repository = AsyncMock()
        service.storefront_repo = AsyncMock()
        service.platform_repo = AsyncMock()
        service.encryption = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_get_by_id_without_decrypt(self, service, mock_credential):
        """Test getting credential without decryption."""
        service.repository.get_with_relations.return_value = mock_credential

        credential, decrypted = await service.get_by_id(1, decrypt=False)

        assert credential == mock_credential
        assert decrypted is None

    @pytest.mark.asyncio
    async def test_get_by_id_with_decrypt(self, service, mock_credential):
        """Test getting credential with decryption."""
        service.repository.get_with_relations.return_value = mock_credential
        service.encryption.decrypt.return_value = {"access_token": "secret"}

        credential, decrypted = await service.get_by_id(1, decrypt=True)

        assert credential == mock_credential
        assert decrypted == {"access_token": "secret"}

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service):
        """Test NotFoundError when credential doesn't exist."""
        service.repository.get_with_relations.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_id(999)

    @pytest.mark.asyncio
    async def test_create_success(
        self, service, mock_credential, mock_storefront, mock_platform
    ):
        """Test successful credential creation."""
        service.storefront_repo.get_by_id.return_value = mock_storefront
        service.platform_repo.get_by_id.return_value = mock_platform
        service.repository.credential_exists.return_value = False
        service.encryption.encrypt.return_value = "encrypted"
        service.repository.create.return_value = mock_credential

        data = CredentialCreate(
            storefront_id=1,
            platform_id=1,
            credentials={"access_token": "secret"},
        )

        result = await service.create(data)

        assert result == mock_credential
        service.encryption.encrypt.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_storefront_not_found(self, service):
        """Test NotFoundError when storefront doesn't exist."""
        service.storefront_repo.get_by_id.return_value = None

        data = CredentialCreate(
            storefront_id=999,
            platform_id=1,
            credentials={"access_token": "secret"},
        )

        with pytest.raises(NotFoundError) as exc:
            await service.create(data)

        assert "Storefront" in str(exc.value)

    @pytest.mark.asyncio
    async def test_create_platform_not_found(self, service, mock_storefront):
        """Test NotFoundError when platform doesn't exist."""
        service.storefront_repo.get_by_id.return_value = mock_storefront
        service.platform_repo.get_by_id.return_value = None

        data = CredentialCreate(
            storefront_id=1,
            platform_id=999,
            credentials={"access_token": "secret"},
        )

        with pytest.raises(NotFoundError) as exc:
            await service.create(data)

        assert "Platform" in str(exc.value)

    @pytest.mark.asyncio
    async def test_create_duplicate_fails(
        self, service, mock_storefront, mock_platform
    ):
        """Test ConflictError when credential already exists."""
        service.storefront_repo.get_by_id.return_value = mock_storefront
        service.platform_repo.get_by_id.return_value = mock_platform
        service.repository.credential_exists.return_value = True

        data = CredentialCreate(
            storefront_id=1,
            platform_id=1,
            credentials={"access_token": "secret"},
        )

        with pytest.raises(ConflictError):
            await service.create(data)

    @pytest.mark.asyncio
    async def test_update_with_new_credentials(self, service, mock_credential):
        """Test updating credential with new encrypted credentials."""
        service.repository.get_with_relations.return_value = mock_credential
        service.encryption.encrypt.return_value = "new_encrypted"
        updated = MagicMock()
        service.repository.update.return_value = updated

        data = CredentialUpdate(
            credentials={"access_token": "new_secret"},
            is_active=False,
        )

        result = await service.update(1, data)

        service.encryption.encrypt.assert_called_once()
        service.repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_without_credentials(self, service, mock_credential):
        """Test updating credential without changing credentials."""
        service.repository.get_with_relations.return_value = mock_credential
        updated = MagicMock()
        updated.is_active = False
        service.repository.update.return_value = updated

        data = CredentialUpdate(is_active=False)

        result = await service.update(1, data)

        service.encryption.encrypt.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_success(self, service, mock_credential):
        """Test successful credential deletion."""
        service.repository.get_with_relations.return_value = mock_credential
        service.repository.delete.return_value = True

        result = await service.delete(1)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_by_storefront(self, service, mock_credential):
        """Test getting credentials by storefront."""
        service.repository.get_by_storefront.return_value = [mock_credential]

        result = await service.get_by_storefront(1)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_active_for_event(self, service, mock_credential):
        """Test getting active credentials for event processing."""
        service.repository.get_active_credentials_for_event.return_value = [
            mock_credential
        ]

        result = await service.get_active_for_event(1)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_mark_used(self, service):
        """Test marking credential as used."""
        await service.mark_used(1, error="Some error")

        service.repository.update_last_used.assert_called_once_with(1, error="Some error")


# ============================================================================
# SgtmConfigService Tests
# ============================================================================


class TestSgtmConfigService:
    """Tests for SgtmConfigService."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def mock_config(self):
        """Create mock sGTM config."""
        config = MagicMock(spec=StorefrontSgtmConfig)
        config.id = 1
        config.storefront_id = 1
        config.sgtm_url = "https://tags.example.com"
        config.client_type = SgtmClientType.GA4
        config.measurement_id = "G-XXXXXX"
        config.api_secret = "encrypted_secret"
        config.is_active = True
        return config

    @pytest.fixture
    def mock_storefront(self):
        storefront = MagicMock(spec=Storefront)
        storefront.id = 1
        return storefront

    @pytest.fixture
    def service(self, mock_session):
        service = SgtmConfigService(mock_session)
        service.repository = AsyncMock()
        service.storefront_repo = AsyncMock()
        service.encryption = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, service, mock_config):
        """Test successful retrieval by ID."""
        service.repository.get_by_id.return_value = mock_config

        result = await service.get_by_id(1)

        assert result == mock_config

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service):
        """Test NotFoundError when config doesn't exist."""
        service.repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_id(999)

    @pytest.mark.asyncio
    async def test_get_by_storefront_id_success(self, service, mock_config):
        """Test getting config by storefront ID."""
        service.repository.get_by_storefront_id.return_value = mock_config

        result = await service.get_by_storefront_id(1)

        assert result == mock_config

    @pytest.mark.asyncio
    async def test_get_by_storefront_id_not_found(self, service):
        """Test NotFoundError when config for storefront doesn't exist."""
        service.repository.get_by_storefront_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_storefront_id(999)

    @pytest.mark.asyncio
    async def test_create_success(self, service, mock_config, mock_storefront):
        """Test successful config creation."""
        service.storefront_repo.get_by_id.return_value = mock_storefront
        service.repository.config_exists_for_storefront.return_value = False
        service.encryption.encrypt.return_value = "encrypted"
        service.repository.create.return_value = mock_config

        data = SgtmConfigCreate(
            storefront_id=1,
            sgtm_url="https://tags.example.com",
            client_type="ga4",
            measurement_id="G-XXXXXX",
            api_secret="secret",
        )

        result = await service.create(data)

        assert result == mock_config
        service.encryption.encrypt.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_without_api_secret(self, service, mock_config, mock_storefront):
        """Test creating config without api_secret."""
        service.storefront_repo.get_by_id.return_value = mock_storefront
        service.repository.config_exists_for_storefront.return_value = False
        service.repository.create.return_value = mock_config

        data = SgtmConfigCreate(
            storefront_id=1,
            sgtm_url="https://tags.example.com",
            client_type="custom",
        )

        result = await service.create(data)

        service.encryption.encrypt.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_storefront_not_found(self, service):
        """Test NotFoundError when storefront doesn't exist."""
        service.storefront_repo.get_by_id.return_value = None

        data = SgtmConfigCreate(
            storefront_id=999,
            sgtm_url="https://tags.example.com",
            client_type="ga4",
            measurement_id="G-XXXXXX",
        )

        with pytest.raises(NotFoundError):
            await service.create(data)

    @pytest.mark.asyncio
    async def test_create_duplicate_fails(self, service, mock_storefront):
        """Test ConflictError when config already exists for storefront."""
        service.storefront_repo.get_by_id.return_value = mock_storefront
        service.repository.config_exists_for_storefront.return_value = True

        data = SgtmConfigCreate(
            storefront_id=1,
            sgtm_url="https://tags.example.com",
            client_type="ga4",
            measurement_id="G-XXXXXX",
        )

        with pytest.raises(ConflictError):
            await service.create(data)

    @pytest.mark.asyncio
    async def test_update_success(self, service, mock_config):
        """Test successful config update."""
        service.repository.get_by_id.return_value = mock_config
        updated = MagicMock()
        updated.sgtm_url = "https://new-tags.example.com"
        service.repository.update.return_value = updated

        data = SgtmConfigUpdate(sgtm_url="https://new-tags.example.com")

        result = await service.update(1, data)

        assert result.sgtm_url == "https://new-tags.example.com"

    @pytest.mark.asyncio
    async def test_update_with_api_secret(self, service, mock_config):
        """Test updating config with new api_secret."""
        service.repository.get_by_id.return_value = mock_config
        service.encryption.encrypt.return_value = "new_encrypted"
        service.repository.update.return_value = mock_config

        data = SgtmConfigUpdate(api_secret="new_secret")

        await service.update(1, data)

        service.encryption.encrypt.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success(self, service, mock_config):
        """Test successful config deletion."""
        service.repository.get_by_id.return_value = mock_config
        service.repository.delete.return_value = True

        result = await service.delete(1)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_decrypted_secret(self, service, mock_config):
        """Test getting decrypted API secret."""
        service.repository.get_by_id.return_value = mock_config
        service.encryption.decrypt.return_value = {"api_secret": "decrypted_secret"}

        result = await service.get_decrypted_secret(1)

        assert result == "decrypted_secret"

    @pytest.mark.asyncio
    async def test_get_decrypted_secret_none(self, service, mock_config):
        """Test getting decrypted secret when none exists."""
        mock_config.api_secret = None
        service.repository.get_by_id.return_value = mock_config

        result = await service.get_decrypted_secret(1)

        assert result is None


# ============================================================================
# EventService Tests
# ============================================================================


class TestEventService:
    """Tests for EventService."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def mock_event(self):
        """Create mock event."""
        event = MagicMock(spec=MarketingEvent)
        event.id = 1
        event.event_id = "evt_001"
        event.storefront_id = 1
        event.event_type = "purchase"
        event.event_payload = json.dumps({"value": 99.99})
        event.status = EventStatus.PENDING
        event.retry_count = 0
        return event

    @pytest.fixture
    def mock_storefront(self):
        storefront = MagicMock(spec=Storefront)
        storefront.id = 1
        storefront.storefront_id = "test-store"
        storefront.is_active = True
        return storefront

    @pytest.fixture
    def service(self, mock_session):
        service = EventService(mock_session)
        service.repository = AsyncMock()
        service.storefront_repo = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, service, mock_event):
        """Test successful retrieval by ID."""
        service.repository.get_by_id.return_value = mock_event

        result = await service.get_by_id(1)

        assert result == mock_event

    @pytest.mark.asyncio
    async def test_get_by_id_with_attempts(self, service, mock_event):
        """Test retrieval by ID with attempts."""
        service.repository.get_with_attempts.return_value = mock_event

        result = await service.get_by_id(1, with_attempts=True)

        service.repository.get_with_attempts.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service):
        """Test NotFoundError when event doesn't exist."""
        service.repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_id(999)

    @pytest.mark.asyncio
    async def test_get_by_event_id_success(self, service, mock_event):
        """Test retrieval by external event_id."""
        service.repository.get_by_event_id.return_value = mock_event

        result = await service.get_by_event_id("evt_001")

        assert result == mock_event

    @pytest.mark.asyncio
    async def test_ingest_batch_success(self, service, mock_storefront):
        """Test successful batch ingestion."""
        service.storefront_repo.get_by_storefront_id.return_value = mock_storefront
        service.repository.event_id_exists.return_value = False
        service.repository.bulk_create.return_value = None

        batch = EventBatchRequest(
            count=1,
            data=[
                EventDataItem(
                    storefront_id="test-store",
                    event_name="purchase",
                    event_time=datetime.utcnow(),
                    order_id="order_001",
                )
            ],
            error="",
        )

        accepted, errors = await service.ingest_batch(batch)

        assert len(accepted) == 1
        assert "order_001" in accepted
        assert len(errors) == 0
        service.repository.bulk_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_batch_with_batch_error(self, service):
        """Test batch ingestion fails with batch error."""
        batch = EventBatchRequest(
            count=0,
            data=[],
            error="OMS database connection failed",
        )

        with pytest.raises(ValidationError) as exc:
            await service.ingest_batch(batch)

        assert "database connection" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_ingest_batch_unknown_storefront(self, service):
        """Test batch ingestion with unknown storefront."""
        service.storefront_repo.get_by_storefront_id.return_value = None

        batch = EventBatchRequest(
            count=1,
            data=[
                EventDataItem(
                    storefront_id="unknown-store",
                    event_name="purchase",
                    event_time=datetime.utcnow(),
                    order_id="order_001",
                )
            ],
            error="",
        )

        accepted, errors = await service.ingest_batch(batch)

        assert len(accepted) == 0
        assert len(errors) == 1
        assert "not found" in errors[0]["error"].lower()

    @pytest.mark.asyncio
    async def test_ingest_batch_inactive_storefront(self, service, mock_storefront):
        """Test batch ingestion with inactive storefront."""
        mock_storefront.is_active = False
        service.storefront_repo.get_by_storefront_id.return_value = mock_storefront

        batch = EventBatchRequest(
            count=1,
            data=[
                EventDataItem(
                    storefront_id="test-store",
                    event_name="purchase",
                    event_time=datetime.utcnow(),
                    order_id="order_001",
                )
            ],
            error="",
        )

        accepted, errors = await service.ingest_batch(batch)

        assert len(accepted) == 0
        assert len(errors) == 1
        assert "disabled" in errors[0]["error"].lower()

    @pytest.mark.asyncio
    async def test_ingest_batch_duplicate_event(self, service, mock_storefront):
        """Test batch ingestion with duplicate event_id."""
        service.storefront_repo.get_by_storefront_id.return_value = mock_storefront
        service.repository.event_id_exists.return_value = True

        batch = EventBatchRequest(
            count=1,
            data=[
                EventDataItem(
                    storefront_id="test-store",
                    event_name="purchase",
                    event_time=datetime.utcnow(),
                    order_id="duplicate_order",
                )
            ],
            error="",
        )

        accepted, errors = await service.ingest_batch(batch)

        assert len(accepted) == 0
        assert len(errors) == 1
        assert "already exists" in errors[0]["error"].lower()

    @pytest.mark.asyncio
    async def test_ingest_batch_partial_success(self, service, mock_storefront):
        """Test batch ingestion with mix of valid and invalid events."""
        service.storefront_repo.get_by_storefront_id.side_effect = [
            mock_storefront,  # First event - valid
            None,  # Second event - unknown store
        ]
        service.repository.event_id_exists.return_value = False

        batch = EventBatchRequest(
            count=2,
            data=[
                EventDataItem(
                    storefront_id="test-store",
                    event_name="purchase",
                    event_time=datetime.utcnow(),
                    order_id="order_001",
                ),
                EventDataItem(
                    storefront_id="unknown-store",
                    event_name="purchase",
                    event_time=datetime.utcnow(),
                    order_id="order_002",
                ),
            ],
            error="",
        )

        # Need to handle the caching behavior
        service._storefront_cache = {}

        accepted, errors = await service.ingest_batch(batch)

        assert len(accepted) == 1
        assert len(errors) == 1

    @pytest.mark.asyncio
    async def test_get_pending_events(self, service, mock_event):
        """Test getting pending events."""
        service.repository.get_pending_events.return_value = [mock_event]

        result = await service.get_pending_events()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_events_for_retry(self, service, mock_event):
        """Test getting events for retry."""
        mock_event.status = EventStatus.RETRYING
        service.repository.get_events_for_retry.return_value = [mock_event]

        result = await service.get_events_for_retry()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_mark_processing(self, service):
        """Test marking event as processing."""
        await service.mark_processing(1)

        service.repository.update_status.assert_called_once_with(
            1, EventStatus.PROCESSING
        )

    @pytest.mark.asyncio
    async def test_mark_delivered(self, service):
        """Test marking event as delivered."""
        await service.mark_delivered(1)

        service.repository.update_status.assert_called_once()
        call_args = service.repository.update_status.call_args
        assert call_args[0][1] == EventStatus.DELIVERED

    @pytest.mark.asyncio
    async def test_mark_failed_with_retry(self, service, mock_event):
        """Test marking event as failed with retry scheduling."""
        service.repository.get_by_id.return_value = mock_event

        with patch("app.services.event_service.settings") as mock_settings:
            mock_settings.max_retry_attempts = 5
            mock_settings.retry_backoff_base = 60

            await service.mark_failed(1, "Connection timeout", can_retry=True)

        call_args = service.repository.update_status.call_args
        assert call_args[0][1] == EventStatus.RETRYING

    @pytest.mark.asyncio
    async def test_mark_failed_max_retries_exceeded(self, service, mock_event):
        """Test marking event as failed when max retries exceeded."""
        mock_event.retry_count = 5  # Already at max
        service.repository.get_by_id.return_value = mock_event

        with patch("app.services.event_service.settings") as mock_settings:
            mock_settings.max_retry_attempts = 5

            await service.mark_failed(1, "Connection timeout", can_retry=True)

        call_args = service.repository.update_status.call_args
        assert call_args[0][1] == EventStatus.FAILED

    @pytest.mark.asyncio
    async def test_mark_failed_no_retry(self, service, mock_event):
        """Test marking event as failed without retry."""
        service.repository.get_by_id.return_value = mock_event

        await service.mark_failed(1, "Permanent failure", can_retry=False)

        call_args = service.repository.update_status.call_args
        assert call_args[0][1] == EventStatus.FAILED

    @pytest.mark.asyncio
    async def test_get_by_storefront(self, service, mock_event):
        """Test getting events by storefront."""
        service.repository.get_by_storefront.return_value = [mock_event]

        result = await service.get_by_storefront(1, status=EventStatus.PENDING)

        assert len(result) == 1


# ============================================================================
# ForwardingService Tests
# ============================================================================


class TestForwardingService:
    """Tests for ForwardingService."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def mock_event(self):
        """Create mock event."""
        event = MagicMock(spec=MarketingEvent)
        event.id = 1
        event.event_id = "evt_001"
        event.storefront_id = 1
        event.event_type = "purchase"
        event.event_payload = json.dumps({"value": 99.99})
        event.status = EventStatus.PENDING
        return event

    @pytest.fixture
    def mock_credential(self):
        """Create mock credential."""
        credential = MagicMock(spec=PlatformCredential)
        credential.id = 1
        credential.storefront_id = 1
        credential.credentials_encrypted = "encrypted"
        credential.destination_type = DestinationType.SGTM
        credential.pixel_id = "pixel_123"
        credential.account_id = "account_456"

        # Mock related objects
        credential.platform = MagicMock()
        credential.platform.is_active = True
        credential.platform.platform_code = "meta_capi"

        credential.storefront = MagicMock()
        credential.storefront.is_active = True

        return credential

    @pytest.fixture
    def mock_sgtm_config(self):
        """Create mock sGTM config."""
        config = MagicMock(spec=StorefrontSgtmConfig)
        config.id = 1
        config.sgtm_url = "https://tags.example.com"
        config.is_active = True
        return config

    @pytest.fixture
    def service(self, mock_session):
        service = ForwardingService(mock_session)
        service.event_repo = AsyncMock()
        service.credential_repo = AsyncMock()
        service.sgtm_repo = AsyncMock()
        service.attempt_repo = AsyncMock()
        service.encryption = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_process_event_success(
        self, service, mock_event, mock_credential, mock_sgtm_config
    ):
        """Test successful event processing."""
        service.credential_repo.get_active_credentials_for_event.return_value = [
            mock_credential
        ]
        service.encryption.decrypt.return_value = {"access_token": "token"}
        service.sgtm_repo.get_by_storefront_id.return_value = mock_sgtm_config

        # Mock adapter
        mock_adapter = AsyncMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.status_code = 200
        mock_result.response_body = '{"status": "ok"}'
        mock_result.error_message = None
        mock_adapter.send.return_value = mock_result

        with patch("app.adapters.factory.get_adapter", return_value=mock_adapter):
            result = await service.process_event(mock_event)

        assert result is True
        service.event_repo.update_status.assert_called()

    @pytest.mark.asyncio
    async def test_process_event_no_credentials(self, service, mock_event):
        """Test event processing with no active credentials."""
        service.credential_repo.get_active_credentials_for_event.return_value = []

        result = await service.process_event(mock_event)

        assert result is False
        call_args = service.event_repo.update_status.call_args
        assert call_args[0][1] == EventStatus.FAILED

    @pytest.mark.asyncio
    async def test_process_event_invalid_payload(self, service, mock_event):
        """Test event processing with invalid JSON payload."""
        mock_event.event_payload = "invalid json"
        service.credential_repo.get_active_credentials_for_event.return_value = [
            MagicMock()
        ]

        result = await service.process_event(mock_event)

        assert result is False

    @pytest.mark.asyncio
    async def test_process_event_skip_inactive_platform(
        self, service, mock_event, mock_credential
    ):
        """Test that inactive platforms are skipped."""
        mock_credential.platform.is_active = False
        service.credential_repo.get_active_credentials_for_event.return_value = [
            mock_credential
        ]

        result = await service.process_event(mock_event)

        # Should fail since no active platforms
        assert result is False

    @pytest.mark.asyncio
    async def test_process_event_skip_inactive_storefront(
        self, service, mock_event, mock_credential
    ):
        """Test that events for inactive storefronts are skipped."""
        mock_credential.storefront.is_active = False
        service.credential_repo.get_active_credentials_for_event.return_value = [
            mock_credential
        ]

        result = await service.process_event(mock_event)

        assert result is False

    @pytest.mark.asyncio
    async def test_process_event_delivery_failure(
        self, service, mock_event, mock_credential, mock_sgtm_config
    ):
        """Test event processing with delivery failure."""
        service.credential_repo.get_active_credentials_for_event.return_value = [
            mock_credential
        ]
        service.encryption.decrypt.return_value = {"access_token": "token"}
        service.sgtm_repo.get_by_storefront_id.return_value = mock_sgtm_config

        # Mock adapter with failure
        mock_adapter = AsyncMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.status_code = 500
        mock_result.response_body = '{"error": "internal error"}'
        mock_result.error_message = "Server error"
        mock_adapter.send.return_value = mock_result

        with patch("app.adapters.factory.get_adapter", return_value=mock_adapter):
            with patch.object(service, "_deliver_to_credential") as mock_deliver:
                mock_deliver.return_value = (False, "Server error")
                result = await service.process_event(mock_event)

        assert result is False

    @pytest.mark.asyncio
    async def test_process_event_sgtm_config_inactive(
        self, service, mock_event, mock_credential
    ):
        """Test event processing when sGTM config is inactive."""
        service.credential_repo.get_active_credentials_for_event.return_value = [
            mock_credential
        ]
        service.encryption.decrypt.return_value = {"access_token": "token"}

        # sGTM config is inactive
        mock_config = MagicMock()
        mock_config.is_active = False
        service.sgtm_repo.get_by_storefront_id.return_value = mock_config

        result = await service.process_event(mock_event)

        # Should record failed attempt
        assert result is False

    @pytest.mark.asyncio
    async def test_process_batch_success(self, service, mock_event):
        """Test batch processing."""
        service.event_repo.get_pending_events.return_value = [mock_event]

        with patch.object(service, "process_event", return_value=True):
            stats = await service.process_batch(limit=10)

        assert stats["processed"] == 1
        assert stats["succeeded"] == 1
        assert stats["failed"] == 0

    @pytest.mark.asyncio
    async def test_process_batch_mixed_results(self, service):
        """Test batch processing with mixed success/failure."""
        event1 = MagicMock()
        event1.id = 1
        event2 = MagicMock()
        event2.id = 2

        service.event_repo.get_pending_events.return_value = [event1, event2]

        with patch.object(
            service, "process_event", side_effect=[True, False]
        ):
            stats = await service.process_batch(limit=10)

        assert stats["processed"] == 2
        assert stats["succeeded"] == 1
        assert stats["failed"] == 1

    @pytest.mark.asyncio
    async def test_process_batch_exception(self, service):
        """Test batch processing when exception occurs."""
        event = MagicMock()
        event.id = 1
        service.event_repo.get_pending_events.return_value = [event]

        with patch.object(
            service, "process_event", side_effect=Exception("Unexpected error")
        ):
            stats = await service.process_batch(limit=10)

        assert stats["failed"] == 1

    @pytest.mark.asyncio
    async def test_process_retries(self, service, mock_event):
        """Test retry processing."""
        mock_event.status = EventStatus.RETRYING
        service.event_repo.get_events_for_retry.return_value = [mock_event]

        with patch.object(service, "process_event", return_value=True):
            stats = await service.process_retries(limit=10)

        assert stats["succeeded"] == 1

    @pytest.mark.asyncio
    async def test_deliver_to_credential_kill_switch(
        self, service, mock_event, mock_credential
    ):
        """Test delivery when kill switch is active."""
        service.encryption.decrypt.return_value = {"access_token": "token"}
        service.sgtm_repo.get_by_storefront_id.return_value = None  # No config

        payload = {"value": 99.99}

        success, error = await service._deliver_to_credential(
            mock_event, mock_credential, payload
        )

        assert success is False
        assert error is not None
        service.attempt_repo.create_attempt.assert_called_once()
