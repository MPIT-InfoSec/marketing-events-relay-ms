"""Pytest configuration and fixtures for Marketing Events Relay tests."""

import asyncio
import base64
import json
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_db
from app.core.security import CredentialEncryption
from app.main import app
from app.models.base import Base
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

# Test database URL (SQLite in-memory for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ============================================================================
# Session and Event Loop Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests."""
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# ============================================================================
# Client Fixtures
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with database override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sync_client(async_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Create sync test client for simple tests."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as tc:
        yield tc

    app.dependency_overrides.clear()


# ============================================================================
# Authentication Fixtures
# ============================================================================


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Return auth headers for protected endpoints."""
    credentials = f"{settings.basic_auth_username}:{settings.basic_auth_password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


@pytest.fixture
def invalid_auth_headers() -> dict[str, str]:
    """Return invalid auth headers for testing auth failures."""
    credentials = "invalid_user:wrong_password"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


# ============================================================================
# Encryption Fixtures
# ============================================================================


@pytest.fixture
def encryption() -> CredentialEncryption:
    """Return encryption instance for tests."""
    return CredentialEncryption()


@pytest.fixture
def test_encryption_key() -> str:
    """Generate a test encryption key."""
    return CredentialEncryption.generate_key()


# ============================================================================
# Storefront Data Fixtures
# ============================================================================


@pytest.fixture
def sample_storefront_data() -> dict[str, Any]:
    """Sample storefront data for tests."""
    return {
        "storefront_id": "test-store-001",
        "name": "Test Store",
        "domain": "teststore.com",
        "description": "A test storefront for unit tests",
        "is_active": True,
    }


@pytest.fixture
def sample_storefront_data_inactive() -> dict[str, Any]:
    """Sample inactive storefront data."""
    return {
        "storefront_id": "inactive-store-001",
        "name": "Inactive Store",
        "domain": "inactivestore.com",
        "description": "An inactive storefront",
        "is_active": False,
    }


@pytest.fixture
def multiple_storefronts_data() -> list[dict[str, Any]]:
    """Multiple storefronts for testing list operations."""
    return [
        {
            "storefront_id": "bosley",
            "name": "Bosley Store",
            "domain": "bosley.com",
            "is_active": True,
        },
        {
            "storefront_id": "pfizer",
            "name": "Pfizer Store",
            "domain": "pfizer.com",
            "is_active": True,
        },
        {
            "storefront_id": "inactive-store",
            "name": "Inactive Store",
            "domain": "inactive.com",
            "is_active": False,
        },
    ]


# ============================================================================
# Platform Data Fixtures
# ============================================================================


@pytest.fixture
def sample_platform_data() -> dict[str, Any]:
    """Sample platform data for tests."""
    return {
        "platform_code": "test_platform",
        "name": "Test Platform",
        "category": "advertising",
        "tier": 2,
        "auth_type": "access_token",
        "api_base_url": "https://api.testplatform.com",
        "credential_schema": '{"access_token": "string", "pixel_id": "string"}',
        "description": "A test advertising platform",
        "is_active": True,
    }


@pytest.fixture
def sample_meta_platform_data() -> dict[str, Any]:
    """Sample Meta/Facebook platform data."""
    return {
        "platform_code": "meta_capi",
        "name": "Meta Conversions API",
        "category": "advertising",
        "tier": 1,
        "auth_type": "access_token",
        "api_base_url": "https://graph.facebook.com/v18.0",
        "credential_schema": '{"access_token": "string"}',
        "description": "Meta Conversions API for Facebook/Instagram ads",
        "is_active": True,
    }


@pytest.fixture
def sample_ga4_platform_data() -> dict[str, Any]:
    """Sample GA4 platform data."""
    return {
        "platform_code": "ga4",
        "name": "Google Analytics 4",
        "category": "analytics",
        "tier": 1,
        "auth_type": "api_key",
        "api_base_url": "https://www.google-analytics.com",
        "credential_schema": '{"measurement_id": "string", "api_secret": "string"}',
        "description": "Google Analytics 4 Measurement Protocol",
        "is_active": True,
    }


@pytest.fixture
def multiple_platforms_data() -> list[dict[str, Any]]:
    """Multiple platforms for testing list operations."""
    return [
        {
            "platform_code": "meta_capi",
            "name": "Meta CAPI",
            "category": "advertising",
            "tier": 1,
            "auth_type": "access_token",
            "is_active": True,
        },
        {
            "platform_code": "ga4",
            "name": "Google Analytics 4",
            "category": "analytics",
            "tier": 1,
            "auth_type": "api_key",
            "is_active": True,
        },
        {
            "platform_code": "tiktok_events",
            "name": "TikTok Events API",
            "category": "advertising",
            "tier": 2,
            "auth_type": "access_token",
            "is_active": True,
        },
        {
            "platform_code": "inactive_platform",
            "name": "Inactive Platform",
            "category": "advertising",
            "tier": 3,
            "auth_type": "access_token",
            "is_active": False,
        },
    ]


# ============================================================================
# Credential Data Fixtures
# ============================================================================


@pytest.fixture
def sample_credentials() -> dict[str, str]:
    """Sample credentials for encryption tests."""
    return {
        "access_token": "EAAGm0PX4ZCps_test_token_123456789",
        "pixel_id": "123456789012345",
    }


@pytest.fixture
def sample_ga4_credentials() -> dict[str, str]:
    """Sample GA4 credentials."""
    return {
        "measurement_id": "G-XXXXXXXXXX",
        "api_secret": "abcdef123456",
    }


# ============================================================================
# sGTM Config Data Fixtures
# ============================================================================


@pytest.fixture
def sample_sgtm_config_ga4() -> dict[str, Any]:
    """Sample sGTM config for GA4 client type."""
    return {
        "sgtm_url": "https://tags.example.com",
        "client_type": "ga4",
        "container_id": "GTM-XXXXXX",
        "measurement_id": "G-XXXXXX",
        "api_secret": "test_api_secret",
        "is_active": True,
    }


@pytest.fixture
def sample_sgtm_config_custom() -> dict[str, Any]:
    """Sample sGTM config for custom client type."""
    return {
        "sgtm_url": "https://tags.example.com",
        "client_type": "custom",
        "custom_endpoint_path": "/events/collect",
        "custom_headers": {"X-Api-Key": "test-api-key", "X-Source": "marketing-relay"},
        "is_active": True,
    }


# ============================================================================
# Event Data Fixtures
# ============================================================================


@pytest.fixture
def sample_event_payload() -> dict[str, Any]:
    """Sample event payload for tests."""
    return {
        "currency": "USD",
        "value": 99.99,
        "transaction_id": "txn_test_001",
        "order_id": "order_12345",
        "items": [
            {
                "item_id": "SKU001",
                "item_name": "Test Product",
                "quantity": 1,
                "price": 99.99,
            }
        ],
        "user_data": {
            "email": "test@example.com",
            "phone": "+1234567890",
        },
        "utm_source": "google",
        "utm_medium": "cpc",
        "utm_campaign": "test_campaign",
    }


@pytest.fixture
def sample_event_data_item() -> dict[str, Any]:
    """Sample event data item from OMS batch format."""
    return {
        "t-value": "bosleyaffiliate_0123",
        "storefront_id": "bosley",
        "event_name": "purchase_completed",
        "event_time": "2026-01-15T10:25:00Z",
        "order_id": "2025020100003333",
        "order_created_date": "2026-01-15T10:25:00Z",
        "order_ship_date": "2026-01-15T10:25:00Z",
        "order_revenue": 80.79,
        "session_id": "sess_456",
        "utm_source": "google",
        "utm_medium": "organic",
        "utm_campaign": "bosley_q1",
    }


@pytest.fixture
def sample_event_batch() -> dict[str, Any]:
    """Sample event batch from OMS."""
    return {
        "count": 3,
        "data": [
            {
                "t-value": "bosleyaffiliate_0123",
                "storefront_id": "bosley",
                "event_name": "consult_started",
                "event_time": "2026-01-15T10:15:00Z",
                "order_id": "2025010100001111",
                "session_id": "sess_123",
                "utm_source": "facebook",
                "utm_medium": "cpc",
                "utm_campaign": "bosley_q1",
            },
            {
                "t-value": "pfizeraffiliate_0123",
                "storefront_id": "pfizer",
                "event_name": "rx_issued",
                "event_time": "2026-01-15T10:20:30Z",
                "order_id": "2025010100002222",
                "session_id": "sess_789",
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "pfizer_q1",
            },
            {
                "t-value": "bosleyaffiliate_0123",
                "storefront_id": "bosley",
                "event_name": "purchase_completed",
                "event_time": "2026-01-15T10:25:00Z",
                "order_id": "2025020100003333",
                "order_created_date": "2026-01-15T10:25:00Z",
                "order_ship_date": "2026-01-15T10:25:00Z",
                "order_revenue": 80.79,
                "session_id": "sess_456",
                "utm_source": "google",
                "utm_medium": "organic",
                "utm_campaign": "bosley_q1",
            },
        ],
        "error": "",
        "next_index": 1000,
        "next_url": "https://oms.example.com/events?offset=1000",
        "previous_index": "",
        "previous_url": "",
    }


@pytest.fixture
def sample_event_batch_single_storefront() -> dict[str, Any]:
    """Sample event batch with events for a single storefront."""
    return {
        "count": 2,
        "data": [
            {
                "storefront_id": "test-store-001",
                "event_name": "purchase_completed",
                "event_time": "2026-01-15T10:00:00Z",
                "order_id": "order_001",
                "order_revenue": 50.00,
            },
            {
                "storefront_id": "test-store-001",
                "event_name": "add_to_cart",
                "event_time": "2026-01-15T10:05:00Z",
                "order_id": "order_002",
            },
        ],
        "error": "",
    }


# ============================================================================
# Database Model Fixtures (for repository/service tests)
# ============================================================================


@pytest_asyncio.fixture
async def db_storefront(async_session: AsyncSession) -> Storefront:
    """Create a storefront in the test database."""
    storefront = Storefront(
        storefront_id="test-store-001",
        name="Test Store",
        domain="teststore.com",
        description="Test storefront",
        is_active=True,
    )
    async_session.add(storefront)
    await async_session.commit()
    await async_session.refresh(storefront)
    return storefront


@pytest_asyncio.fixture
async def db_inactive_storefront(async_session: AsyncSession) -> Storefront:
    """Create an inactive storefront in the test database."""
    storefront = Storefront(
        storefront_id="inactive-store",
        name="Inactive Store",
        domain="inactive.com",
        is_active=False,
    )
    async_session.add(storefront)
    await async_session.commit()
    await async_session.refresh(storefront)
    return storefront


@pytest_asyncio.fixture
async def db_platform(async_session: AsyncSession) -> AdAnalyticsPlatform:
    """Create a platform in the test database."""
    platform = AdAnalyticsPlatform(
        platform_code="test_platform",
        name="Test Platform",
        category="advertising",
        tier=2,
        auth_type=AuthType.ACCESS_TOKEN,
        api_base_url="https://api.test.com",
        is_active=True,
    )
    async_session.add(platform)
    await async_session.commit()
    await async_session.refresh(platform)
    return platform


@pytest_asyncio.fixture
async def db_sgtm_config(
    async_session: AsyncSession, db_storefront: Storefront, encryption: CredentialEncryption
) -> StorefrontSgtmConfig:
    """Create sGTM config in the test database."""
    config = StorefrontSgtmConfig(
        storefront_id=db_storefront.id,
        sgtm_url="https://tags.example.com",
        client_type=SgtmClientType.GA4,
        container_id="GTM-XXXXXX",
        measurement_id="G-XXXXXX",
        api_secret=encryption.encrypt({"api_secret": "test_secret"}),
        is_active=True,
    )
    async_session.add(config)
    await async_session.commit()
    await async_session.refresh(config)
    return config


@pytest_asyncio.fixture
async def db_credential(
    async_session: AsyncSession,
    db_storefront: Storefront,
    db_platform: AdAnalyticsPlatform,
    encryption: CredentialEncryption,
) -> PlatformCredential:
    """Create a platform credential in the test database."""
    credential = PlatformCredential(
        storefront_id=db_storefront.id,
        platform_id=db_platform.id,
        credentials_encrypted=encryption.encrypt({"access_token": "test_token_123"}),
        destination_type=DestinationType.SGTM,
        pixel_id="pixel_123",
        account_id="account_456",
        is_active=True,
    )
    async_session.add(credential)
    await async_session.commit()
    await async_session.refresh(credential)
    return credential


@pytest_asyncio.fixture
async def db_event(
    async_session: AsyncSession, db_storefront: Storefront
) -> MarketingEvent:
    """Create a marketing event in the test database."""
    event = MarketingEvent(
        event_id="evt_test_001",
        storefront_id=db_storefront.id,
        event_type="purchase",
        event_payload=json.dumps({"value": 99.99, "currency": "USD"}),
        source_system="oms",
        status=EventStatus.PENDING,
    )
    async_session.add(event)
    await async_session.commit()
    await async_session.refresh(event)
    return event


@pytest_asyncio.fixture
async def db_event_retrying(
    async_session: AsyncSession, db_storefront: Storefront
) -> MarketingEvent:
    """Create a retrying event in the test database."""
    event = MarketingEvent(
        event_id="evt_retry_001",
        storefront_id=db_storefront.id,
        event_type="purchase",
        event_payload=json.dumps({"value": 50.00}),
        source_system="oms",
        status=EventStatus.RETRYING,
        retry_count=1,
        next_retry_at=datetime.utcnow() - timedelta(minutes=5),  # Ready for retry
        error_message="Previous attempt failed",
    )
    async_session.add(event)
    await async_session.commit()
    await async_session.refresh(event)
    return event


@pytest_asyncio.fixture
async def db_event_attempt(
    async_session: AsyncSession,
    db_event: MarketingEvent,
    db_credential: PlatformCredential,
) -> EventAttempt:
    """Create an event attempt in the test database."""
    attempt = EventAttempt(
        event_id=db_event.id,
        credential_id=db_credential.id,
        destination_type=DestinationType.SGTM,
        status=AttemptStatus.SUCCESS,
        http_status_code=200,
        response_body='{"status": "ok"}',
        duration_ms=150,
    )
    async_session.add(attempt)
    await async_session.commit()
    await async_session.refresh(attempt)
    return attempt


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for adapter tests."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"status": "ok"}'

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)

    return mock_client


@pytest.fixture
def mock_sgtm_config():
    """Mock sGTM config object for adapter tests."""
    config = MagicMock()
    config.sgtm_url = "https://tags.example.com"
    config.client_type = SgtmClientType.GA4
    config.measurement_id = "G-XXXXXX"
    config.api_secret = "test_api_secret"
    config.custom_endpoint_path = "/collect"
    config.custom_headers = None
    config.is_active = True
    return config


@pytest.fixture
def mock_sgtm_config_custom():
    """Mock sGTM config for custom client type."""
    config = MagicMock()
    config.sgtm_url = "https://tags.example.com"
    config.client_type = SgtmClientType.CUSTOM
    config.measurement_id = None
    config.api_secret = None
    config.custom_endpoint_path = "/events/collect"
    config.custom_headers = {"X-Api-Key": "test-key"}
    config.is_active = True
    return config


# ============================================================================
# Helper Functions
# ============================================================================


def generate_unique_id(prefix: str = "test") -> str:
    """Generate a unique ID for test data."""
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:8]}"
