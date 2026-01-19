"""Unit tests for Pydantic schemas."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.enums import DestinationType, SgtmClientType
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.credential import CredentialCreate, CredentialUpdate
from app.schemas.event import (
    EventBatchRequest,
    EventBatchResponse,
    EventCreate,
    EventDataItem,
)
from app.schemas.platform import PlatformCreate, PlatformUpdate
from app.schemas.sgtm_config import SgtmConfigCreate, SgtmConfigUpdate
from app.schemas.storefront import StorefrontCreate, StorefrontUpdate


# ============================================================================
# Storefront Schema Tests
# ============================================================================


class TestStorefrontCreate:
    """Tests for StorefrontCreate schema."""

    def test_valid_storefront_create(self):
        """Test valid storefront creation."""
        data = StorefrontCreate(
            storefront_id="test-store-123",
            name="Test Store",
            domain="test.com",
        )

        assert data.storefront_id == "test-store-123"
        assert data.name == "Test Store"
        assert data.domain == "test.com"
        assert data.is_active is True  # Default value

    def test_storefront_id_lowercased(self):
        """Test that storefront_id is normalized to lowercase."""
        data = StorefrontCreate(
            storefront_id="TEST-STORE-123",
            name="Test Store",
        )

        assert data.storefront_id == "test-store-123"

    def test_storefront_id_with_underscores(self):
        """Test storefront_id with underscores is valid."""
        data = StorefrontCreate(
            storefront_id="test_store_123",
            name="Test Store",
        )

        assert data.storefront_id == "test_store_123"

    def test_storefront_id_with_hyphens(self):
        """Test storefront_id with hyphens is valid."""
        data = StorefrontCreate(
            storefront_id="test-store-123",
            name="Test Store",
        )

        assert data.storefront_id == "test-store-123"

    def test_storefront_id_mixed_valid_characters(self):
        """Test storefront_id with mixed valid characters."""
        data = StorefrontCreate(
            storefront_id="test-store_123-abc",
            name="Test Store",
        )

        assert data.storefront_id == "test-store_123-abc"

    def test_invalid_storefront_id_special_chars(self):
        """Test that storefront_id with special characters fails."""
        with pytest.raises(ValidationError) as exc_info:
            StorefrontCreate(
                storefront_id="test store!@#",
                name="Test Store",
            )

        assert "storefront_id" in str(exc_info.value)

    def test_invalid_storefront_id_spaces(self):
        """Test that storefront_id with spaces fails."""
        with pytest.raises(ValidationError):
            StorefrontCreate(
                storefront_id="test store",
                name="Test Store",
            )

    def test_storefront_id_empty_fails(self):
        """Test that empty storefront_id fails."""
        with pytest.raises(ValidationError):
            StorefrontCreate(
                storefront_id="",
                name="Test Store",
            )

    def test_storefront_id_too_long_fails(self):
        """Test that storefront_id exceeding max length fails."""
        with pytest.raises(ValidationError):
            StorefrontCreate(
                storefront_id="a" * 51,  # Max is 50
                name="Test Store",
            )

    def test_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValidationError):
            StorefrontCreate(
                storefront_id="test-store",
            )

    def test_name_min_length(self):
        """Test name minimum length validation."""
        with pytest.raises(ValidationError):
            StorefrontCreate(
                storefront_id="test-store",
                name="",
            )

    def test_optional_fields_can_be_none(self):
        """Test optional fields can be omitted."""
        data = StorefrontCreate(
            storefront_id="test-store",
            name="Test Store",
        )

        assert data.domain is None
        assert data.description is None

    def test_is_active_default_true(self):
        """Test is_active defaults to True."""
        data = StorefrontCreate(
            storefront_id="test-store",
            name="Test Store",
        )

        assert data.is_active is True

    def test_is_active_can_be_false(self):
        """Test is_active can be set to False."""
        data = StorefrontCreate(
            storefront_id="test-store",
            name="Test Store",
            is_active=False,
        )

        assert data.is_active is False


class TestStorefrontUpdate:
    """Tests for StorefrontUpdate schema."""

    def test_all_fields_optional(self):
        """Test all fields are optional for update."""
        data = StorefrontUpdate()

        assert data.name is None
        assert data.domain is None
        assert data.description is None
        assert data.is_active is None

    def test_partial_update(self):
        """Test partial update with only some fields."""
        data = StorefrontUpdate(
            name="Updated Name",
            is_active=False,
        )

        assert data.name == "Updated Name"
        assert data.is_active is False
        assert data.domain is None


# ============================================================================
# Platform Schema Tests
# ============================================================================


class TestPlatformCreate:
    """Tests for PlatformCreate schema."""

    def test_valid_platform_create(self):
        """Test valid platform creation."""
        data = PlatformCreate(
            platform_code="my_platform",
            name="My Platform",
            tier=2,
        )

        assert data.platform_code == "my_platform"
        assert data.tier == 2
        assert data.is_active is True

    def test_platform_code_lowercased(self):
        """Test that platform_code is normalized to lowercase."""
        data = PlatformCreate(
            platform_code="MY_PLATFORM",
            name="My Platform",
        )

        assert data.platform_code == "my_platform"

    def test_platform_code_with_underscores(self):
        """Test platform_code with underscores is valid."""
        data = PlatformCreate(
            platform_code="meta_capi_v2",
            name="Meta CAPI v2",
        )

        assert data.platform_code == "meta_capi_v2"

    def test_invalid_platform_code_hyphen(self):
        """Test that platform_code with hyphens fails."""
        with pytest.raises(ValidationError):
            PlatformCreate(
                platform_code="my-platform",
                name="My Platform",
            )

    def test_invalid_platform_code_special_chars(self):
        """Test that platform_code with special characters fails."""
        with pytest.raises(ValidationError):
            PlatformCreate(
                platform_code="my_platform!",
                name="My Platform",
            )

    def test_valid_tier_1(self):
        """Test tier 1 is valid."""
        data = PlatformCreate(
            platform_code="critical_platform",
            name="Critical Platform",
            tier=1,
        )

        assert data.tier == 1

    def test_valid_tier_3(self):
        """Test tier 3 is valid."""
        data = PlatformCreate(
            platform_code="standard_platform",
            name="Standard Platform",
            tier=3,
        )

        assert data.tier == 3

    def test_invalid_tier_0(self):
        """Test tier 0 is invalid."""
        with pytest.raises(ValidationError):
            PlatformCreate(
                platform_code="my_platform",
                name="My Platform",
                tier=0,
            )

    def test_invalid_tier_4(self):
        """Test tier > 3 is invalid."""
        with pytest.raises(ValidationError):
            PlatformCreate(
                platform_code="my_platform",
                name="My Platform",
                tier=4,
            )

    def test_invalid_tier_negative(self):
        """Test negative tier is invalid."""
        with pytest.raises(ValidationError):
            PlatformCreate(
                platform_code="my_platform",
                name="My Platform",
                tier=-1,
            )

    def test_default_tier(self):
        """Test default tier value."""
        data = PlatformCreate(
            platform_code="my_platform",
            name="My Platform",
        )

        # Default should be 2 or defined in schema
        assert data.tier in [1, 2, 3]

    def test_auth_type_valid_values(self):
        """Test valid auth_type values."""
        valid_auth_types = ["api_key", "oauth2", "access_token", "bearer_token", "basic_auth"]

        for auth_type in valid_auth_types:
            data = PlatformCreate(
                platform_code=f"platform_{auth_type.replace('_', '')}",
                name="Test Platform",
                auth_type=auth_type,
            )
            assert data.auth_type == auth_type


class TestPlatformUpdate:
    """Tests for PlatformUpdate schema."""

    def test_all_fields_optional(self):
        """Test all fields are optional for update."""
        data = PlatformUpdate()

        assert data.name is None
        assert data.tier is None
        assert data.is_active is None

    def test_partial_update(self):
        """Test partial update."""
        data = PlatformUpdate(
            tier=1,
            is_active=False,
        )

        assert data.tier == 1
        assert data.is_active is False


# ============================================================================
# Credential Schema Tests
# ============================================================================


class TestCredentialCreate:
    """Tests for CredentialCreate schema."""

    def test_valid_credential_create(self):
        """Test valid credential creation."""
        data = CredentialCreate(
            storefront_id=1,
            platform_id=1,
            credentials={"access_token": "test_token"},
        )

        assert data.storefront_id == 1
        assert data.platform_id == 1
        assert data.credentials == {"access_token": "test_token"}
        assert data.destination_type == DestinationType.SGTM  # Default

    def test_destination_type_sgtm(self):
        """Test destination_type sgtm."""
        data = CredentialCreate(
            storefront_id=1,
            platform_id=1,
            credentials={"access_token": "test"},
            destination_type=DestinationType.SGTM,
        )

        assert data.destination_type == DestinationType.SGTM

    def test_destination_type_direct(self):
        """Test destination_type direct."""
        data = CredentialCreate(
            storefront_id=1,
            platform_id=1,
            credentials={"access_token": "test"},
            destination_type=DestinationType.DIRECT,
        )

        assert data.destination_type == DestinationType.DIRECT

    def test_credentials_dict(self):
        """Test credentials as dictionary."""
        credentials = {
            "access_token": "EAAGm0PX4ZCps...",
            "pixel_id": "123456789",
            "api_secret": "secret_key",
        }

        data = CredentialCreate(
            storefront_id=1,
            platform_id=1,
            credentials=credentials,
        )

        assert data.credentials == credentials

    def test_optional_pixel_id(self):
        """Test optional pixel_id field."""
        data = CredentialCreate(
            storefront_id=1,
            platform_id=1,
            credentials={"access_token": "test"},
            pixel_id="pixel_123",
        )

        assert data.pixel_id == "pixel_123"

    def test_optional_account_id(self):
        """Test optional account_id field."""
        data = CredentialCreate(
            storefront_id=1,
            platform_id=1,
            credentials={"access_token": "test"},
            account_id="account_456",
        )

        assert data.account_id == "account_456"


class TestCredentialUpdate:
    """Tests for CredentialUpdate schema."""

    def test_all_fields_optional(self):
        """Test all fields are optional for update."""
        data = CredentialUpdate()

        assert data.credentials is None
        assert data.is_active is None

    def test_partial_update_credentials(self):
        """Test partial update with new credentials."""
        data = CredentialUpdate(
            credentials={"access_token": "new_token"},
        )

        assert data.credentials == {"access_token": "new_token"}

    def test_partial_update_is_active(self):
        """Test partial update for is_active."""
        data = CredentialUpdate(
            is_active=False,
        )

        assert data.is_active is False


# ============================================================================
# sGTM Config Schema Tests
# ============================================================================


class TestSgtmConfigCreate:
    """Tests for SgtmConfigCreate schema."""

    def test_valid_ga4_config(self):
        """Test valid sGTM config for GA4 client."""
        data = SgtmConfigCreate(
            storefront_id=1,
            sgtm_url="https://gtm.example.com",
            client_type=SgtmClientType.GA4,
            measurement_id="G-XXXXXX",
            container_id="GTM-XXXXXX",
        )

        assert data.sgtm_url == "https://gtm.example.com"
        assert data.client_type == SgtmClientType.GA4
        assert data.measurement_id == "G-XXXXXX"
        assert data.is_active is True

    def test_valid_custom_config(self):
        """Test valid sGTM config for custom client."""
        data = SgtmConfigCreate(
            storefront_id=1,
            sgtm_url="https://gtm.example.com",
            client_type=SgtmClientType.CUSTOM,
            custom_endpoint_path="/events",
            custom_headers={"X-Api-Key": "test-key"},
        )

        assert data.client_type == SgtmClientType.CUSTOM
        assert data.custom_endpoint_path == "/events"
        assert data.custom_headers == {"X-Api-Key": "test-key"}

    def test_sgtm_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from sgtm_url."""
        data = SgtmConfigCreate(
            storefront_id=1,
            sgtm_url="https://gtm.example.com/",
            client_type=SgtmClientType.CUSTOM,
        )

        assert data.sgtm_url == "https://gtm.example.com"

    def test_invalid_sgtm_url_no_protocol(self):
        """Test that sGTM URL without protocol fails."""
        with pytest.raises(ValidationError):
            SgtmConfigCreate(
                storefront_id=1,
                sgtm_url="gtm.example.com",
            )

    def test_invalid_sgtm_url_not_url(self):
        """Test that non-URL string fails."""
        with pytest.raises(ValidationError):
            SgtmConfigCreate(
                storefront_id=1,
                sgtm_url="not-a-url",
            )

    def test_valid_container_id_format(self):
        """Test valid GTM container ID format."""
        data = SgtmConfigCreate(
            storefront_id=1,
            sgtm_url="https://gtm.example.com",
            client_type=SgtmClientType.CUSTOM,
            container_id="GTM-ABC123",
        )

        assert data.container_id == "GTM-ABC123"

    def test_invalid_container_id_format(self):
        """Test that invalid container_id format fails."""
        with pytest.raises(ValidationError):
            SgtmConfigCreate(
                storefront_id=1,
                sgtm_url="https://gtm.example.com",
                container_id="INVALID-123",
            )

    def test_valid_measurement_id_format(self):
        """Test valid GA4 measurement ID format."""
        data = SgtmConfigCreate(
            storefront_id=1,
            sgtm_url="https://gtm.example.com",
            client_type=SgtmClientType.GA4,
            measurement_id="G-ABC123DEF",
        )

        assert data.measurement_id == "G-ABC123DEF"

    def test_invalid_measurement_id_format(self):
        """Test that invalid measurement_id format fails."""
        with pytest.raises(ValidationError):
            SgtmConfigCreate(
                storefront_id=1,
                sgtm_url="https://gtm.example.com",
                measurement_id="INVALID",
            )

    def test_ga4_client_requires_measurement_id(self):
        """Test that GA4 client type requires measurement_id."""
        with pytest.raises(ValidationError) as exc_info:
            SgtmConfigCreate(
                storefront_id=1,
                sgtm_url="https://gtm.example.com",
                client_type=SgtmClientType.GA4,
            )

        assert "measurement_id" in str(exc_info.value).lower()

    def test_custom_endpoint_path_adds_leading_slash(self):
        """Test that leading slash is added to custom_endpoint_path."""
        data = SgtmConfigCreate(
            storefront_id=1,
            sgtm_url="https://gtm.example.com",
            client_type=SgtmClientType.CUSTOM,
            custom_endpoint_path="events",
        )

        assert data.custom_endpoint_path == "/events"

    def test_custom_endpoint_path_preserves_leading_slash(self):
        """Test that existing leading slash is preserved."""
        data = SgtmConfigCreate(
            storefront_id=1,
            sgtm_url="https://gtm.example.com",
            client_type=SgtmClientType.CUSTOM,
            custom_endpoint_path="/events",
        )

        assert data.custom_endpoint_path == "/events"


class TestSgtmConfigUpdate:
    """Tests for SgtmConfigUpdate schema."""

    def test_all_fields_optional(self):
        """Test all fields are optional for update."""
        data = SgtmConfigUpdate()

        assert data.sgtm_url is None
        assert data.client_type is None
        assert data.is_active is None

    def test_partial_update(self):
        """Test partial update."""
        data = SgtmConfigUpdate(
            sgtm_url="https://new-gtm.example.com",
            is_active=False,
        )

        assert data.sgtm_url == "https://new-gtm.example.com"
        assert data.is_active is False


# ============================================================================
# Event Schema Tests
# ============================================================================


class TestEventDataItem:
    """Tests for EventDataItem schema (OMS batch format)."""

    def test_valid_event_data_item(self):
        """Test valid event data item."""
        data = EventDataItem(
            storefront_id="bosley",
            event_name="purchase_completed",
            event_time="2026-01-15T10:25:00Z",
            order_id="2025020100003333",
        )

        assert data.storefront_id == "bosley"
        assert data.event_name == "purchase_completed"
        assert data.order_id == "2025020100003333"

    def test_event_data_item_with_t_value_alias(self):
        """Test t-value field alias."""
        data = EventDataItem(
            **{
                "t-value": "bosleyaffiliate_0123",
                "storefront_id": "bosley",
                "event_name": "purchase",
                "event_time": "2026-01-15T10:25:00Z",
                "order_id": "order_123",
            }
        )

        assert data.t_value == "bosleyaffiliate_0123"

    def test_event_data_item_optional_fields(self):
        """Test optional fields are None by default."""
        data = EventDataItem(
            storefront_id="bosley",
            event_name="purchase",
            event_time="2026-01-15T10:25:00Z",
            order_id="order_123",
        )

        assert data.t_value is None
        assert data.session_id is None
        assert data.utm_source is None
        assert data.order_revenue is None

    def test_event_data_item_with_revenue(self):
        """Test event with order revenue."""
        data = EventDataItem(
            storefront_id="bosley",
            event_name="purchase_completed",
            event_time="2026-01-15T10:25:00Z",
            order_id="order_123",
            order_revenue=80.79,
        )

        assert data.order_revenue == 80.79

    def test_event_data_item_with_utm_params(self):
        """Test event with UTM parameters."""
        data = EventDataItem(
            storefront_id="bosley",
            event_name="purchase",
            event_time="2026-01-15T10:25:00Z",
            order_id="order_123",
            utm_source="google",
            utm_medium="cpc",
            utm_campaign="spring_sale",
        )

        assert data.utm_source == "google"
        assert data.utm_medium == "cpc"
        assert data.utm_campaign == "spring_sale"

    def test_to_event_payload_basic(self):
        """Test to_event_payload conversion."""
        data = EventDataItem(
            storefront_id="bosley",
            event_name="purchase",
            event_time=datetime(2026, 1, 15, 10, 25, 0),
            order_id="order_123",
        )

        payload = data.to_event_payload()

        assert payload["order_id"] == "order_123"
        assert "event_time" in payload

    def test_to_event_payload_with_revenue(self):
        """Test to_event_payload includes revenue and value."""
        data = EventDataItem(
            storefront_id="bosley",
            event_name="purchase",
            event_time=datetime(2026, 1, 15, 10, 25, 0),
            order_id="order_123",
            order_revenue=99.99,
        )

        payload = data.to_event_payload()

        assert payload["order_revenue"] == 99.99
        assert payload["value"] == 99.99  # For platform compatibility

    def test_to_event_payload_with_all_fields(self):
        """Test to_event_payload with all optional fields."""
        data = EventDataItem(
            **{
                "t-value": "affiliate_123",
                "storefront_id": "bosley",
                "event_name": "purchase",
                "event_time": datetime(2026, 1, 15, 10, 25, 0),
                "order_id": "order_123",
                "session_id": "sess_456",
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "campaign_1",
                "order_created_date": datetime(2026, 1, 15, 10, 0, 0),
                "order_ship_date": datetime(2026, 1, 16, 10, 0, 0),
                "order_revenue": 150.00,
            }
        )

        payload = data.to_event_payload()

        assert payload["t_value"] == "affiliate_123"
        assert payload["session_id"] == "sess_456"
        assert payload["utm_source"] == "google"
        assert payload["utm_medium"] == "cpc"
        assert payload["utm_campaign"] == "campaign_1"
        assert "order_created_date" in payload
        assert "order_ship_date" in payload


class TestEventBatchRequest:
    """Tests for EventBatchRequest schema."""

    def test_valid_batch_request(self):
        """Test valid batch request."""
        data = EventBatchRequest(
            count=2,
            data=[
                EventDataItem(
                    storefront_id="bosley",
                    event_name="purchase",
                    event_time="2026-01-15T10:25:00Z",
                    order_id="order_1",
                ),
                EventDataItem(
                    storefront_id="pfizer",
                    event_name="rx_issued",
                    event_time="2026-01-15T10:30:00Z",
                    order_id="order_2",
                ),
            ],
            error="",
        )

        assert data.count == 2
        assert len(data.data) == 2

    def test_batch_request_with_pagination(self):
        """Test batch request with pagination fields."""
        data = EventBatchRequest(
            count=100,
            data=[
                EventDataItem(
                    storefront_id="bosley",
                    event_name="purchase",
                    event_time="2026-01-15T10:25:00Z",
                    order_id="order_1",
                ),
            ],
            error="",
            next_index=100,
            next_url="https://oms.example.com/events?offset=100",
        )

        assert data.next_index == 100
        assert data.next_url == "https://oms.example.com/events?offset=100"

    def test_empty_data_without_error_fails(self):
        """Test that empty data without error fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            EventBatchRequest(
                count=0,
                data=[],
                error="",
            )

        assert "data cannot be empty" in str(exc_info.value).lower()

    def test_empty_data_with_error_allowed(self):
        """Test that empty data with error is allowed."""
        data = EventBatchRequest(
            count=0,
            data=[],
            error="Database connection failed",
        )

        assert data.error == "Database connection failed"
        assert len(data.data) == 0

    def test_full_oms_batch_format_from_dict(self):
        """Test parsing exact OMS batch format from raw dict (as from API request)."""
        # This is the exact format that OMS sends
        raw_data = {
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

        # Parse as the API would
        data = EventBatchRequest(**raw_data)

        # Verify all top-level fields
        assert data.count == 3
        assert len(data.data) == 3
        assert data.error == ""
        assert data.next_index == 1000
        assert data.next_url == "https://oms.example.com/events?offset=1000"
        assert data.previous_index == ""
        assert data.previous_url == ""

        # Verify first event (bosley consult_started)
        event1 = data.data[0]
        assert event1.t_value == "bosleyaffiliate_0123"
        assert event1.storefront_id == "bosley"
        assert event1.event_name == "consult_started"
        assert event1.order_id == "2025010100001111"
        assert event1.session_id == "sess_123"
        assert event1.utm_source == "facebook"
        assert event1.utm_medium == "cpc"
        assert event1.utm_campaign == "bosley_q1"

        # Verify second event (pfizer rx_issued)
        event2 = data.data[1]
        assert event2.t_value == "pfizeraffiliate_0123"
        assert event2.storefront_id == "pfizer"
        assert event2.event_name == "rx_issued"
        assert event2.order_id == "2025010100002222"

        # Verify third event (bosley purchase_completed with revenue and dates)
        event3 = data.data[2]
        assert event3.t_value == "bosleyaffiliate_0123"
        assert event3.storefront_id == "bosley"
        assert event3.event_name == "purchase_completed"
        assert event3.order_id == "2025020100003333"
        assert event3.order_revenue == 80.79
        assert event3.order_created_date is not None
        assert event3.order_ship_date is not None

        # Verify to_event_payload for third event includes all fields
        payload = event3.to_event_payload()
        assert payload["t_value"] == "bosleyaffiliate_0123"
        assert payload["order_revenue"] == 80.79
        assert payload["value"] == 80.79  # For platform compatibility
        assert payload["utm_source"] == "google"
        assert payload["utm_medium"] == "organic"
        assert "order_created_date" in payload
        assert "order_ship_date" in payload


class TestEventCreate:
    """Tests for EventCreate schema (legacy format)."""

    def test_valid_event_create(self):
        """Test valid event creation."""
        data = EventCreate(
            event_id="evt_123",
            event_type="purchase",
            event_payload={"value": 99.99, "currency": "USD"},
        )

        assert data.event_id == "evt_123"
        assert data.event_type == "purchase"
        assert data.source_system == "oms"  # Default

    def test_event_type_lowercased(self):
        """Test that event_type is normalized to lowercase."""
        data = EventCreate(
            event_id="evt_123",
            event_type="PURCHASE",
            event_payload={"value": 99.99},
        )

        assert data.event_type == "purchase"

    def test_event_id_required(self):
        """Test that event_id is required."""
        with pytest.raises(ValidationError):
            EventCreate(
                event_type="purchase",
                event_payload={"value": 99.99},
            )

    def test_event_id_min_length(self):
        """Test event_id minimum length."""
        with pytest.raises(ValidationError):
            EventCreate(
                event_id="",
                event_type="purchase",
                event_payload={"value": 99.99},
            )

    def test_event_id_max_length(self):
        """Test event_id maximum length."""
        with pytest.raises(ValidationError):
            EventCreate(
                event_id="e" * 101,  # Max is 100
                event_type="purchase",
                event_payload={"value": 99.99},
            )


class TestEventBatchResponse:
    """Tests for EventBatchResponse schema."""

    def test_successful_batch_response(self):
        """Test successful batch response."""
        data = EventBatchResponse(
            accepted=5,
            rejected=0,
            event_ids=["evt_1", "evt_2", "evt_3", "evt_4", "evt_5"],
            errors=[],
        )

        assert data.accepted == 5
        assert data.rejected == 0
        assert len(data.event_ids) == 5

    def test_partial_batch_response(self):
        """Test partial success batch response."""
        data = EventBatchResponse(
            accepted=3,
            rejected=2,
            event_ids=["evt_1", "evt_2", "evt_3"],
            errors=[
                {"event_id": "evt_4", "error": "Storefront not found"},
                {"event_id": "evt_5", "error": "Event already exists"},
            ],
        )

        assert data.accepted == 3
        assert data.rejected == 2
        assert len(data.errors) == 2


# ============================================================================
# Common Schema Tests
# ============================================================================


class TestPaginationParams:
    """Tests for PaginationParams schema."""

    def test_default_values(self):
        """Test default pagination values."""
        params = PaginationParams()

        assert params.skip == 0
        assert params.limit == 100

    def test_custom_values(self):
        """Test custom pagination values."""
        params = PaginationParams(skip=50, limit=25)

        assert params.skip == 50
        assert params.limit == 25


class TestPaginatedResponse:
    """Tests for PaginatedResponse schema."""

    def test_paginated_response_creation(self):
        """Test creating paginated response."""
        response = PaginatedResponse.create(
            items=[{"id": 1}, {"id": 2}],
            total=10,
            skip=0,
            limit=2,
        )

        assert len(response.items) == 2
        assert response.total == 10
        assert response.skip == 0
        assert response.limit == 2
        assert response.has_more is True

    def test_paginated_response_no_more(self):
        """Test paginated response when no more items."""
        response = PaginatedResponse.create(
            items=[{"id": 1}, {"id": 2}],
            total=2,
            skip=0,
            limit=10,
        )

        assert response.has_more is False

    def test_paginated_response_empty(self):
        """Test empty paginated response."""
        response = PaginatedResponse.create(
            items=[],
            total=0,
            skip=0,
            limit=10,
        )

        assert len(response.items) == 0
        assert response.total == 0
        assert response.has_more is False
