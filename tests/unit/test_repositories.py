"""Unit tests for repository layer data access."""

import json
from datetime import datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    AttemptStatus,
    AuthType,
    DestinationType,
    EventStatus,
    SgtmClientType,
)
from app.models.credential import PlatformCredential
from app.models.event import MarketingEvent
from app.models.event_attempt import EventAttempt
from app.models.platform import AdAnalyticsPlatform
from app.models.sgtm_config import StorefrontSgtmConfig
from app.models.storefront import Storefront
from app.repositories.base import BaseRepository
from app.repositories.credential_repository import CredentialRepository
from app.repositories.event_attempt_repository import EventAttemptRepository
from app.repositories.event_repository import EventRepository
from app.repositories.platform_repository import PlatformRepository
from app.repositories.sgtm_config_repository import SgtmConfigRepository
from app.repositories.storefront_repository import StorefrontRepository


# ============================================================================
# BaseRepository Tests
# ============================================================================


class TestBaseRepository:
    """Tests for BaseRepository generic CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_by_id(self, async_session: AsyncSession, db_storefront: Storefront):
        """Test getting entity by ID."""
        repo = BaseRepository(Storefront, async_session)

        result = await repo.get_by_id(db_storefront.id)

        assert result is not None
        assert result.id == db_storefront.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, async_session: AsyncSession):
        """Test getting non-existent entity by ID."""
        repo = BaseRepository(Storefront, async_session)

        result = await repo.get_by_id(99999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self, async_session: AsyncSession, db_storefront: Storefront):
        """Test getting all entities."""
        repo = BaseRepository(Storefront, async_session)

        results = await repo.get_all()

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, async_session: AsyncSession):
        """Test pagination in get_all."""
        repo = BaseRepository(Storefront, async_session)

        # Create multiple storefronts
        for i in range(5):
            storefront = Storefront(
                storefront_id=f"store-{i}",
                name=f"Store {i}",
                is_active=True,
            )
            async_session.add(storefront)
        await async_session.commit()

        # Test pagination
        page1 = await repo.get_all(skip=0, limit=2)
        page2 = await repo.get_all(skip=2, limit=2)

        assert len(page1) == 2
        assert len(page2) == 2

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, async_session: AsyncSession):
        """Test filtering in get_all."""
        repo = BaseRepository(Storefront, async_session)

        # Create storefronts with different is_active states
        active_sf = Storefront(storefront_id="active-sf", name="Active", is_active=True)
        inactive_sf = Storefront(storefront_id="inactive-sf", name="Inactive", is_active=False)
        async_session.add_all([active_sf, inactive_sf])
        await async_session.commit()

        active_results = await repo.get_all(filters={"is_active": True})
        inactive_results = await repo.get_all(filters={"is_active": False})

        assert all(sf.is_active for sf in active_results)
        assert all(not sf.is_active for sf in inactive_results)

    @pytest.mark.asyncio
    async def test_count(self, async_session: AsyncSession, db_storefront: Storefront):
        """Test counting entities."""
        repo = BaseRepository(Storefront, async_session)

        count = await repo.count()

        assert count >= 1

    @pytest.mark.asyncio
    async def test_count_with_filters(self, async_session: AsyncSession):
        """Test counting with filters."""
        repo = BaseRepository(Storefront, async_session)

        # Create storefronts
        active_sf = Storefront(storefront_id="count-active", name="Active", is_active=True)
        inactive_sf = Storefront(storefront_id="count-inactive", name="Inactive", is_active=False)
        async_session.add_all([active_sf, inactive_sf])
        await async_session.commit()

        active_count = await repo.count(filters={"is_active": True})
        inactive_count = await repo.count(filters={"is_active": False})

        assert active_count >= 1
        assert inactive_count >= 1

    @pytest.mark.asyncio
    async def test_create(self, async_session: AsyncSession):
        """Test creating entity."""
        repo = BaseRepository(Storefront, async_session)

        result = await repo.create({
            "storefront_id": "new-store",
            "name": "New Store",
            "is_active": True,
        })

        assert result.id is not None
        assert result.storefront_id == "new-store"

    @pytest.mark.asyncio
    async def test_update(self, async_session: AsyncSession, db_storefront: Storefront):
        """Test updating entity."""
        repo = BaseRepository(Storefront, async_session)

        result = await repo.update(db_storefront, {"name": "Updated Name"})

        assert result.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete(self, async_session: AsyncSession):
        """Test deleting entity."""
        repo = BaseRepository(Storefront, async_session)

        # Create then delete
        storefront = Storefront(storefront_id="delete-test", name="Delete Test", is_active=True)
        async_session.add(storefront)
        await async_session.commit()

        result = await repo.delete(storefront)

        assert result is True

        # Verify deleted
        deleted = await repo.get_by_id(storefront.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_exists(self, async_session: AsyncSession, db_storefront: Storefront):
        """Test checking entity existence."""
        repo = BaseRepository(Storefront, async_session)

        exists = await repo.exists(db_storefront.id)
        not_exists = await repo.exists(99999)

        assert exists is True
        assert not_exists is False


# ============================================================================
# StorefrontRepository Tests
# ============================================================================


class TestStorefrontRepository:
    """Tests for StorefrontRepository."""

    @pytest.mark.asyncio
    async def test_get_by_storefront_id(
        self, async_session: AsyncSession, db_storefront: Storefront
    ):
        """Test getting storefront by external storefront_id."""
        repo = StorefrontRepository(async_session)

        result = await repo.get_by_storefront_id(db_storefront.storefront_id)

        assert result is not None
        assert result.storefront_id == db_storefront.storefront_id

    @pytest.mark.asyncio
    async def test_get_by_storefront_id_not_found(self, async_session: AsyncSession):
        """Test getting non-existent storefront by storefront_id."""
        repo = StorefrontRepository(async_session)

        result = await repo.get_by_storefront_id("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_config(
        self, async_session: AsyncSession, db_sgtm_config: StorefrontSgtmConfig
    ):
        """Test getting storefront with sGTM config loaded."""
        repo = StorefrontRepository(async_session)

        result = await repo.get_with_config(db_sgtm_config.storefront_id)

        assert result is not None
        # The relationship should be loaded
        assert hasattr(result, "sgtm_config")

    @pytest.mark.asyncio
    async def test_get_with_credentials(
        self, async_session: AsyncSession, db_credential: PlatformCredential
    ):
        """Test getting storefront with credentials loaded."""
        repo = StorefrontRepository(async_session)

        result = await repo.get_with_credentials(db_credential.storefront_id)

        assert result is not None
        assert hasattr(result, "credentials")

    @pytest.mark.asyncio
    async def test_get_active_storefronts(self, async_session: AsyncSession):
        """Test getting only active storefronts."""
        repo = StorefrontRepository(async_session)

        # Create active and inactive storefronts
        active = Storefront(storefront_id="active-test", name="Active", is_active=True)
        inactive = Storefront(storefront_id="inactive-test", name="Inactive", is_active=False)
        async_session.add_all([active, inactive])
        await async_session.commit()

        results = await repo.get_active_storefronts()

        assert all(sf.is_active for sf in results)

    @pytest.mark.asyncio
    async def test_storefront_id_exists(
        self, async_session: AsyncSession, db_storefront: Storefront
    ):
        """Test checking storefront_id existence."""
        repo = StorefrontRepository(async_session)

        exists = await repo.storefront_id_exists(db_storefront.storefront_id)
        not_exists = await repo.storefront_id_exists("nonexistent-store")

        assert exists is True
        assert not_exists is False


# ============================================================================
# PlatformRepository Tests
# ============================================================================


class TestPlatformRepository:
    """Tests for PlatformRepository."""

    @pytest.mark.asyncio
    async def test_get_by_platform_code(
        self, async_session: AsyncSession, db_platform: AdAnalyticsPlatform
    ):
        """Test getting platform by code."""
        repo = PlatformRepository(async_session)

        result = await repo.get_by_platform_code(db_platform.platform_code)

        assert result is not None
        assert result.platform_code == db_platform.platform_code

    @pytest.mark.asyncio
    async def test_get_by_platform_code_not_found(self, async_session: AsyncSession):
        """Test getting non-existent platform by code."""
        repo = PlatformRepository(async_session)

        result = await repo.get_by_platform_code("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_tier(self, async_session: AsyncSession):
        """Test getting platforms by tier."""
        repo = PlatformRepository(async_session)

        # Create platforms with different tiers
        tier1 = AdAnalyticsPlatform(
            platform_code="tier1_platform",
            name="Tier 1 Platform",
            tier=1,
            category="advertising",
            auth_type=AuthType.ACCESS_TOKEN,
            is_active=True,
        )
        tier2 = AdAnalyticsPlatform(
            platform_code="tier2_platform",
            name="Tier 2 Platform",
            tier=2,
            category="advertising",
            auth_type=AuthType.ACCESS_TOKEN,
            is_active=True,
        )
        async_session.add_all([tier1, tier2])
        await async_session.commit()

        results = await repo.get_by_tier(1)

        assert all(p.tier == 1 for p in results)

    @pytest.mark.asyncio
    async def test_get_by_category(self, async_session: AsyncSession):
        """Test getting platforms by category."""
        repo = PlatformRepository(async_session)

        # Create platforms with different categories
        ad_platform = AdAnalyticsPlatform(
            platform_code="ad_platform",
            name="Ad Platform",
            tier=1,
            category="advertising",
            auth_type=AuthType.ACCESS_TOKEN,
            is_active=True,
        )
        analytics_platform = AdAnalyticsPlatform(
            platform_code="analytics_platform",
            name="Analytics Platform",
            tier=1,
            category="analytics",
            auth_type=AuthType.API_KEY,
            is_active=True,
        )
        async_session.add_all([ad_platform, analytics_platform])
        await async_session.commit()

        results = await repo.get_by_category("advertising")

        assert all(p.category == "advertising" for p in results)

    @pytest.mark.asyncio
    async def test_get_active_platforms(self, async_session: AsyncSession):
        """Test getting active platforms ordered by tier."""
        repo = PlatformRepository(async_session)

        # Create active and inactive platforms
        active = AdAnalyticsPlatform(
            platform_code="active_platform",
            name="Active Platform",
            tier=1,
            category="advertising",
            auth_type=AuthType.ACCESS_TOKEN,
            is_active=True,
        )
        inactive = AdAnalyticsPlatform(
            platform_code="inactive_platform",
            name="Inactive Platform",
            tier=1,
            category="advertising",
            auth_type=AuthType.ACCESS_TOKEN,
            is_active=False,
        )
        async_session.add_all([active, inactive])
        await async_session.commit()

        results = await repo.get_active_platforms()

        assert all(p.is_active for p in results)

    @pytest.mark.asyncio
    async def test_platform_code_exists(
        self, async_session: AsyncSession, db_platform: AdAnalyticsPlatform
    ):
        """Test checking platform code existence."""
        repo = PlatformRepository(async_session)

        exists = await repo.platform_code_exists(db_platform.platform_code)
        not_exists = await repo.platform_code_exists("nonexistent")

        assert exists is True
        assert not_exists is False


# ============================================================================
# CredentialRepository Tests
# ============================================================================


class TestCredentialRepository:
    """Tests for CredentialRepository."""

    @pytest.mark.asyncio
    async def test_get_by_storefront_and_platform(
        self, async_session: AsyncSession, db_credential: PlatformCredential
    ):
        """Test getting credential by storefront and platform."""
        repo = CredentialRepository(async_session)

        result = await repo.get_by_storefront_and_platform(
            db_credential.storefront_id,
            db_credential.platform_id,
        )

        assert result is not None
        assert result.storefront_id == db_credential.storefront_id
        assert result.platform_id == db_credential.platform_id

    @pytest.mark.asyncio
    async def test_get_by_storefront_and_platform_not_found(
        self, async_session: AsyncSession
    ):
        """Test getting non-existent credential."""
        repo = CredentialRepository(async_session)

        result = await repo.get_by_storefront_and_platform(99999, 99999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_relations(
        self, async_session: AsyncSession, db_credential: PlatformCredential
    ):
        """Test getting credential with relations loaded."""
        repo = CredentialRepository(async_session)

        result = await repo.get_with_relations(db_credential.id)

        assert result is not None
        assert hasattr(result, "storefront")
        assert hasattr(result, "platform")

    @pytest.mark.asyncio
    async def test_get_by_storefront(
        self, async_session: AsyncSession, db_credential: PlatformCredential
    ):
        """Test getting credentials by storefront."""
        repo = CredentialRepository(async_session)

        results = await repo.get_by_storefront(db_credential.storefront_id)

        assert len(results) >= 1
        assert all(c.storefront_id == db_credential.storefront_id for c in results)

    @pytest.mark.asyncio
    async def test_get_by_storefront_active_only(
        self,
        async_session: AsyncSession,
        db_storefront: Storefront,
        db_platform: AdAnalyticsPlatform,
        encryption,
    ):
        """Test getting only active credentials for storefront."""
        repo = CredentialRepository(async_session)

        # Create active and inactive credentials
        active_cred = PlatformCredential(
            storefront_id=db_storefront.id,
            platform_id=db_platform.id,
            credentials_encrypted=encryption.encrypt({"token": "active"}),
            destination_type=DestinationType.SGTM,
            is_active=True,
        )
        async_session.add(active_cred)
        await async_session.commit()

        results = await repo.get_by_storefront(db_storefront.id, active_only=True)

        assert all(c.is_active for c in results)

    @pytest.mark.asyncio
    async def test_get_active_credentials_for_event(
        self, async_session: AsyncSession, db_credential: PlatformCredential
    ):
        """Test getting active credentials for event processing."""
        repo = CredentialRepository(async_session)

        results = await repo.get_active_credentials_for_event(db_credential.storefront_id)

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_update_last_used(
        self, async_session: AsyncSession, db_credential: PlatformCredential
    ):
        """Test updating last used timestamp."""
        repo = CredentialRepository(async_session)

        await repo.update_last_used(db_credential.id)

        # Refresh and check
        await async_session.refresh(db_credential)
        assert db_credential.last_used_at is not None

    @pytest.mark.asyncio
    async def test_update_last_used_with_error(
        self, async_session: AsyncSession, db_credential: PlatformCredential
    ):
        """Test updating last used with error message."""
        repo = CredentialRepository(async_session)

        await repo.update_last_used(db_credential.id, error="Connection failed")

        await async_session.refresh(db_credential)
        assert db_credential.last_error == "Connection failed"

    @pytest.mark.asyncio
    async def test_credential_exists(
        self, async_session: AsyncSession, db_credential: PlatformCredential
    ):
        """Test checking credential existence."""
        repo = CredentialRepository(async_session)

        exists = await repo.credential_exists(
            db_credential.storefront_id,
            db_credential.platform_id,
        )
        not_exists = await repo.credential_exists(99999, 99999)

        assert exists is True
        assert not_exists is False


# ============================================================================
# SgtmConfigRepository Tests
# ============================================================================


class TestSgtmConfigRepository:
    """Tests for SgtmConfigRepository."""

    @pytest.mark.asyncio
    async def test_get_by_storefront_id(
        self, async_session: AsyncSession, db_sgtm_config: StorefrontSgtmConfig
    ):
        """Test getting config by storefront ID."""
        repo = SgtmConfigRepository(async_session)

        result = await repo.get_by_storefront_id(db_sgtm_config.storefront_id)

        assert result is not None
        assert result.storefront_id == db_sgtm_config.storefront_id

    @pytest.mark.asyncio
    async def test_get_by_storefront_id_not_found(self, async_session: AsyncSession):
        """Test getting non-existent config by storefront ID."""
        repo = SgtmConfigRepository(async_session)

        result = await repo.get_by_storefront_id(99999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_storefront(
        self, async_session: AsyncSession, db_sgtm_config: StorefrontSgtmConfig
    ):
        """Test getting config with storefront loaded."""
        repo = SgtmConfigRepository(async_session)

        result = await repo.get_with_storefront(db_sgtm_config.id)

        assert result is not None
        assert hasattr(result, "storefront")

    @pytest.mark.asyncio
    async def test_get_active_configs(
        self, async_session: AsyncSession, db_sgtm_config: StorefrontSgtmConfig
    ):
        """Test getting active configs."""
        repo = SgtmConfigRepository(async_session)

        results = await repo.get_active_configs()

        assert all(c.is_active for c in results)

    @pytest.mark.asyncio
    async def test_config_exists_for_storefront(
        self, async_session: AsyncSession, db_sgtm_config: StorefrontSgtmConfig
    ):
        """Test checking config existence for storefront."""
        repo = SgtmConfigRepository(async_session)

        exists = await repo.config_exists_for_storefront(db_sgtm_config.storefront_id)
        not_exists = await repo.config_exists_for_storefront(99999)

        assert exists is True
        assert not_exists is False


# ============================================================================
# EventRepository Tests
# ============================================================================


class TestEventRepository:
    """Tests for EventRepository."""

    @pytest.mark.asyncio
    async def test_get_by_event_id(
        self, async_session: AsyncSession, db_event: MarketingEvent
    ):
        """Test getting event by external event_id."""
        repo = EventRepository(async_session)

        result = await repo.get_by_event_id(db_event.event_id)

        assert result is not None
        assert result.event_id == db_event.event_id

    @pytest.mark.asyncio
    async def test_get_by_event_id_not_found(self, async_session: AsyncSession):
        """Test getting non-existent event by event_id."""
        repo = EventRepository(async_session)

        result = await repo.get_by_event_id("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_attempts(
        self, async_session: AsyncSession, db_event_attempt: EventAttempt
    ):
        """Test getting event with attempts loaded."""
        repo = EventRepository(async_session)

        result = await repo.get_with_attempts(db_event_attempt.event_id)

        assert result is not None
        assert hasattr(result, "attempts")

    @pytest.mark.asyncio
    async def test_get_pending_events(
        self, async_session: AsyncSession, db_event: MarketingEvent
    ):
        """Test getting pending events."""
        repo = EventRepository(async_session)

        results = await repo.get_pending_events()

        assert all(e.status == EventStatus.PENDING for e in results)

    @pytest.mark.asyncio
    async def test_get_events_for_retry(
        self, async_session: AsyncSession, db_event_retrying: MarketingEvent
    ):
        """Test getting events ready for retry."""
        repo = EventRepository(async_session)

        results = await repo.get_events_for_retry()

        assert all(e.status == EventStatus.RETRYING for e in results)
        # Should only return events where next_retry_at is in the past
        now = datetime.utcnow()
        assert all(e.next_retry_at <= now for e in results)

    @pytest.mark.asyncio
    async def test_get_by_storefront(
        self, async_session: AsyncSession, db_event: MarketingEvent
    ):
        """Test getting events by storefront."""
        repo = EventRepository(async_session)

        results = await repo.get_by_storefront(db_event.storefront_id)

        assert all(e.storefront_id == db_event.storefront_id for e in results)

    @pytest.mark.asyncio
    async def test_get_by_storefront_with_status_filter(
        self, async_session: AsyncSession, db_event: MarketingEvent
    ):
        """Test getting events by storefront with status filter."""
        repo = EventRepository(async_session)

        results = await repo.get_by_storefront(
            db_event.storefront_id,
            status=EventStatus.PENDING,
        )

        assert all(e.status == EventStatus.PENDING for e in results)

    @pytest.mark.asyncio
    async def test_update_status(
        self, async_session: AsyncSession, db_event: MarketingEvent
    ):
        """Test updating event status."""
        repo = EventRepository(async_session)

        await repo.update_status(db_event.id, EventStatus.PROCESSING)

        await async_session.refresh(db_event)
        assert db_event.status == EventStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_update_status_with_error(
        self, async_session: AsyncSession, db_event: MarketingEvent
    ):
        """Test updating event status with error message."""
        repo = EventRepository(async_session)

        await repo.update_status(
            db_event.id,
            EventStatus.FAILED,
            error_message="Connection timeout",
        )

        await async_session.refresh(db_event)
        assert db_event.status == EventStatus.FAILED
        assert db_event.error_message == "Connection timeout"

    @pytest.mark.asyncio
    async def test_update_status_with_retry(
        self, async_session: AsyncSession, db_event: MarketingEvent
    ):
        """Test updating event status with retry scheduling."""
        repo = EventRepository(async_session)
        next_retry = datetime.utcnow() + timedelta(minutes=5)

        await repo.update_status(
            db_event.id,
            EventStatus.RETRYING,
            error_message="Temporary failure",
            next_retry_at=next_retry,
            increment_retry=True,
        )

        await async_session.refresh(db_event)
        assert db_event.status == EventStatus.RETRYING
        assert db_event.retry_count == 1

    @pytest.mark.asyncio
    async def test_event_id_exists(
        self, async_session: AsyncSession, db_event: MarketingEvent
    ):
        """Test checking event_id existence."""
        repo = EventRepository(async_session)

        exists = await repo.event_id_exists(db_event.event_id)
        not_exists = await repo.event_id_exists("nonexistent")

        assert exists is True
        assert not_exists is False

    @pytest.mark.asyncio
    async def test_bulk_create(
        self, async_session: AsyncSession, db_storefront: Storefront
    ):
        """Test bulk creating events."""
        repo = EventRepository(async_session)

        events = [
            {
                "event_id": f"bulk_evt_{i}",
                "storefront_id": db_storefront.id,
                "event_type": "purchase",
                "event_payload": json.dumps({"value": 10.0 * i}),
                "source_system": "oms",
                "status": EventStatus.PENDING,
            }
            for i in range(5)
        ]

        results = await repo.bulk_create(events)

        assert len(results) == 5
        assert all(e.id is not None for e in results)


# ============================================================================
# EventAttemptRepository Tests
# ============================================================================


class TestEventAttemptRepository:
    """Tests for EventAttemptRepository."""

    @pytest.mark.asyncio
    async def test_get_by_event(
        self, async_session: AsyncSession, db_event_attempt: EventAttempt
    ):
        """Test getting attempts by event."""
        repo = EventAttemptRepository(async_session)

        results = await repo.get_by_event(db_event_attempt.event_id)

        assert len(results) >= 1
        assert all(a.event_id == db_event_attempt.event_id for a in results)

    @pytest.mark.asyncio
    async def test_get_by_credential(
        self, async_session: AsyncSession, db_event_attempt: EventAttempt
    ):
        """Test getting attempts by credential."""
        repo = EventAttemptRepository(async_session)

        results = await repo.get_by_credential(db_event_attempt.credential_id)

        assert len(results) >= 1
        assert all(a.credential_id == db_event_attempt.credential_id for a in results)

    @pytest.mark.asyncio
    async def test_get_recent_attempts(
        self, async_session: AsyncSession, db_event_attempt: EventAttempt
    ):
        """Test getting recent attempts."""
        repo = EventAttemptRepository(async_session)

        results = await repo.get_recent_attempts(hours=24)

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_recent_attempts_with_status(
        self, async_session: AsyncSession, db_event_attempt: EventAttempt
    ):
        """Test getting recent attempts filtered by status."""
        repo = EventAttemptRepository(async_session)

        results = await repo.get_recent_attempts(hours=24, status=AttemptStatus.SUCCESS)

        assert all(a.status == AttemptStatus.SUCCESS for a in results)

    @pytest.mark.asyncio
    async def test_count_by_status(
        self,
        async_session: AsyncSession,
        db_event: MarketingEvent,
        db_credential: PlatformCredential,
    ):
        """Test counting attempts by status for an event."""
        repo = EventAttemptRepository(async_session)

        # Create attempts with different statuses
        success_attempt = EventAttempt(
            event_id=db_event.id,
            credential_id=db_credential.id,
            destination_type=DestinationType.SGTM,
            status=AttemptStatus.SUCCESS,
            http_status_code=200,
        )
        failed_attempt = EventAttempt(
            event_id=db_event.id,
            credential_id=db_credential.id,
            destination_type=DestinationType.SGTM,
            status=AttemptStatus.FAILED,
            error_message="Error",
        )
        async_session.add_all([success_attempt, failed_attempt])
        await async_session.commit()

        counts = await repo.count_by_status(db_event.id)

        assert AttemptStatus.SUCCESS in counts
        assert AttemptStatus.FAILED in counts

    @pytest.mark.asyncio
    async def test_get_success_rate(
        self,
        async_session: AsyncSession,
        db_event: MarketingEvent,
        db_credential: PlatformCredential,
    ):
        """Test calculating success rate for credential."""
        repo = EventAttemptRepository(async_session)

        # Create 3 success and 1 failure
        for i in range(3):
            attempt = EventAttempt(
                event_id=db_event.id,
                credential_id=db_credential.id,
                destination_type=DestinationType.SGTM,
                status=AttemptStatus.SUCCESS,
                http_status_code=200,
            )
            async_session.add(attempt)

        failed = EventAttempt(
            event_id=db_event.id,
            credential_id=db_credential.id,
            destination_type=DestinationType.SGTM,
            status=AttemptStatus.FAILED,
            error_message="Error",
        )
        async_session.add(failed)
        await async_session.commit()

        rate = await repo.get_success_rate(db_credential.id, hours=24)

        assert rate == 0.75  # 3 out of 4

    @pytest.mark.asyncio
    async def test_get_success_rate_no_attempts(
        self, async_session: AsyncSession, db_credential: PlatformCredential
    ):
        """Test success rate returns 1.0 when no attempts exist."""
        repo = EventAttemptRepository(async_session)

        rate = await repo.get_success_rate(db_credential.id, hours=1)

        assert rate == 1.0

    @pytest.mark.asyncio
    async def test_create_attempt(
        self,
        async_session: AsyncSession,
        db_event: MarketingEvent,
        db_credential: PlatformCredential,
    ):
        """Test creating attempt record."""
        repo = EventAttemptRepository(async_session)

        result = await repo.create_attempt(
            event_id=db_event.id,
            credential_id=db_credential.id,
            destination_type=DestinationType.SGTM,
            status=AttemptStatus.SUCCESS,
            http_status_code=200,
            response_body='{"status": "ok"}',
            duration_ms=150,
        )

        assert result.id is not None
        assert result.status == AttemptStatus.SUCCESS
        assert result.http_status_code == 200

    @pytest.mark.asyncio
    async def test_create_attempt_truncates_long_response(
        self,
        async_session: AsyncSession,
        db_event: MarketingEvent,
        db_credential: PlatformCredential,
    ):
        """Test that long response body is truncated."""
        repo = EventAttemptRepository(async_session)

        long_response = "x" * 10000  # Exceeds 5000 char limit

        result = await repo.create_attempt(
            event_id=db_event.id,
            credential_id=db_credential.id,
            destination_type=DestinationType.SGTM,
            status=AttemptStatus.SUCCESS,
            response_body=long_response,
        )

        assert len(result.response_body) == 5000
