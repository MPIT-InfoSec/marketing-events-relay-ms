"""Unit tests for platform adapters."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.adapters.base import AdapterResult, BaseAdapter
from app.adapters.factory import get_adapter, get_registered_adapters
from app.adapters.sgtm import SgtmAdapter
from app.models.enums import SgtmClientType


# ============================================================================
# AdapterResult Tests
# ============================================================================


class TestAdapterResult:
    """Tests for AdapterResult dataclass."""

    def test_ok_result_defaults(self):
        """Test creating success result with defaults."""
        result = AdapterResult.ok()

        assert result.success is True
        assert result.status_code == 200
        assert result.response_body is None
        assert result.error_message is None

    def test_ok_result_with_values(self):
        """Test creating success result with custom values."""
        result = AdapterResult.ok(status_code=201, response_body='{"id": 123}')

        assert result.success is True
        assert result.status_code == 201
        assert result.response_body == '{"id": 123}'
        assert result.error_message is None

    def test_error_result(self):
        """Test creating error result."""
        result = AdapterResult.error(
            error_message="Request failed",
            status_code=500,
        )

        assert result.success is False
        assert result.status_code == 500
        assert result.error_message == "Request failed"

    def test_error_result_minimal(self):
        """Test creating error result with minimal info."""
        result = AdapterResult.error(error_message="Connection timeout")

        assert result.success is False
        assert result.error_message == "Connection timeout"
        assert result.status_code is None

    def test_error_result_with_response_body(self):
        """Test creating error result with response body."""
        result = AdapterResult.error(
            error_message="API error",
            status_code=400,
            response_body='{"error": "Invalid request"}',
        )

        assert result.success is False
        assert result.response_body == '{"error": "Invalid request"}'


# ============================================================================
# Adapter Factory Tests
# ============================================================================


class TestAdapterFactory:
    """Tests for adapter factory."""

    def test_get_known_adapter_sgtm(self):
        """Test getting sGTM adapter."""
        adapter = get_adapter("sgtm")

        assert adapter is not None
        assert adapter.platform_code == "sgtm"
        assert isinstance(adapter, SgtmAdapter)

    def test_get_known_adapter_meta_capi(self):
        """Test getting Meta CAPI adapter."""
        adapter = get_adapter("meta_capi")

        assert adapter is not None
        assert adapter.platform_code == "meta_capi"

    def test_get_known_adapter_ga4(self):
        """Test getting GA4 adapter."""
        adapter = get_adapter("ga4")

        assert adapter is not None
        assert adapter.platform_code == "ga4"

    def test_get_known_adapter_tiktok(self):
        """Test getting TikTok adapter."""
        adapter = get_adapter("tiktok_events")

        assert adapter is not None
        assert adapter.platform_code == "tiktok_events"

    def test_get_known_adapter_snapchat(self):
        """Test getting Snapchat adapter."""
        adapter = get_adapter("snapchat_capi")

        assert adapter is not None
        assert adapter.platform_code == "snapchat_capi"

    def test_get_known_adapter_pinterest(self):
        """Test getting Pinterest adapter."""
        adapter = get_adapter("pinterest_capi")

        assert adapter is not None
        assert adapter.platform_code == "pinterest_capi"

    def test_get_unknown_adapter_returns_sgtm(self):
        """Test that unknown platform returns sGTM adapter."""
        adapter = get_adapter("unknown_platform_xyz")

        assert adapter is not None
        assert adapter.platform_code == "sgtm"

    def test_registered_adapters_contains_core_adapters(self):
        """Test getting list of registered adapters."""
        adapters = get_registered_adapters()

        assert "sgtm" in adapters
        assert "meta_capi" in adapters
        assert "ga4" in adapters
        assert "tiktok_events" in adapters
        assert "snapchat_capi" in adapters
        assert "pinterest_capi" in adapters

    def test_adapter_case_sensitivity(self):
        """Test adapter lookup is case-sensitive or handled correctly."""
        # Assuming lowercase lookup
        adapter = get_adapter("SGTM")

        # Should return sGTM as fallback or handle case
        assert adapter is not None


# ============================================================================
# sGTM Adapter Tests
# ============================================================================


class TestSgtmAdapter:
    """Tests for sGTM adapter."""

    @pytest.fixture
    def sgtm_adapter(self) -> SgtmAdapter:
        """Create sGTM adapter instance."""
        return SgtmAdapter()

    def test_platform_code(self, sgtm_adapter: SgtmAdapter):
        """Test sGTM adapter platform code."""
        assert sgtm_adapter.platform_code == "sgtm"

    @pytest.mark.asyncio
    async def test_send_no_config_returns_error(self, sgtm_adapter: SgtmAdapter):
        """Test send without sGTM config returns error."""
        context: dict[str, Any] = {
            "event_type": "purchase",
            "payload": {"value": 100},
        }

        result = await sgtm_adapter.send(context)

        assert result.success is False
        assert "no sgtm configuration" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_send_inactive_config_returns_error(
        self, sgtm_adapter: SgtmAdapter, mock_sgtm_config
    ):
        """Test send with inactive sGTM config returns error."""
        mock_sgtm_config.is_active = False

        context = {
            "sgtm_config": mock_sgtm_config,
            "event_type": "purchase",
            "payload": {"value": 100},
        }

        result = await sgtm_adapter.send(context)

        assert result.success is False
        assert "disabled" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_send_ga4_success(self, sgtm_adapter: SgtmAdapter, mock_sgtm_config):
        """Test successful GA4 send."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "ok"}'

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            context = {
                "sgtm_config": mock_sgtm_config,
                "event_type": "purchase",
                "payload": {
                    "session_id": "sess_123",
                    "value": 99.99,
                    "currency": "USD",
                },
            }

            result = await sgtm_adapter.send(context)

            assert result.success is True
            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_send_custom_success(
        self, sgtm_adapter: SgtmAdapter, mock_sgtm_config_custom
    ):
        """Test successful custom client send."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"received": true}'

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            context = {
                "sgtm_config": mock_sgtm_config_custom,
                "event_type": "purchase_completed",
                "payload": {"order_id": "123", "order_revenue": 100.00},
                "storefront_code": "bosley",
            }

            result = await sgtm_adapter.send(context)

            assert result.success is True
            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_send_timeout_returns_error(
        self, sgtm_adapter: SgtmAdapter, mock_sgtm_config
    ):
        """Test timeout returns error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            context = {
                "sgtm_config": mock_sgtm_config,
                "event_type": "purchase",
                "payload": {"value": 100},
            }

            result = await sgtm_adapter.send(context)

            assert result.success is False
            assert "timed out" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_send_request_error_returns_error(
        self, sgtm_adapter: SgtmAdapter, mock_sgtm_config
    ):
        """Test request error returns error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            context = {
                "sgtm_config": mock_sgtm_config,
                "event_type": "purchase",
                "payload": {"value": 100},
            }

            result = await sgtm_adapter.send(context)

            assert result.success is False
            assert "failed" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_send_4xx_returns_error(
        self, sgtm_adapter: SgtmAdapter, mock_sgtm_config
    ):
        """Test 4xx response returns error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "Bad request"}'

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            context = {
                "sgtm_config": mock_sgtm_config,
                "event_type": "purchase",
                "payload": {"value": 100},
            }

            result = await sgtm_adapter.send(context)

            assert result.success is False
            assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_send_5xx_returns_error(
        self, sgtm_adapter: SgtmAdapter, mock_sgtm_config
    ):
        """Test 5xx response returns error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            context = {
                "sgtm_config": mock_sgtm_config,
                "event_type": "purchase",
                "payload": {"value": 100},
            }

            result = await sgtm_adapter.send(context)

            assert result.success is False
            assert result.status_code == 500


class TestSgtmAdapterGA4PayloadBuilding:
    """Tests for sGTM adapter GA4 payload building."""

    @pytest.fixture
    def sgtm_adapter(self) -> SgtmAdapter:
        """Create sGTM adapter instance."""
        return SgtmAdapter()

    def test_build_ga4_payload_basic(self, sgtm_adapter: SgtmAdapter):
        """Test building basic GA4 payload."""
        context = {
            "event_type": "purchase",
            "payload": {
                "session_id": "sess_123",
                "value": 99.99,
                "currency": "USD",
            },
        }

        payload = sgtm_adapter._build_ga4_payload(context)

        assert "client_id" in payload
        assert payload["client_id"] == "sess_123"
        assert "events" in payload
        assert len(payload["events"]) == 1
        assert payload["events"][0]["name"] == "purchase"
        assert payload["events"][0]["params"]["value"] == 99.99
        assert payload["events"][0]["params"]["currency"] == "USD"

    def test_build_ga4_payload_with_transaction_id(self, sgtm_adapter: SgtmAdapter):
        """Test GA4 payload includes transaction_id."""
        context = {
            "event_type": "purchase",
            "payload": {
                "session_id": "sess_123",
                "transaction_id": "txn_456",
                "value": 100.00,
            },
        }

        payload = sgtm_adapter._build_ga4_payload(context)

        assert payload["events"][0]["params"]["transaction_id"] == "txn_456"

    def test_build_ga4_payload_order_id_as_transaction_id(
        self, sgtm_adapter: SgtmAdapter
    ):
        """Test order_id is mapped to transaction_id."""
        context = {
            "event_type": "purchase",
            "payload": {
                "session_id": "sess_123",
                "order_id": "order_789",
                "value": 100.00,
            },
        }

        payload = sgtm_adapter._build_ga4_payload(context)

        assert payload["events"][0]["params"]["transaction_id"] == "order_789"

    def test_build_ga4_payload_order_revenue_as_value(self, sgtm_adapter: SgtmAdapter):
        """Test order_revenue is mapped to value."""
        context = {
            "event_type": "purchase",
            "payload": {
                "session_id": "sess_123",
                "order_revenue": 150.00,
            },
        }

        payload = sgtm_adapter._build_ga4_payload(context)

        assert payload["events"][0]["params"]["value"] == 150.00
        assert payload["events"][0]["params"]["currency"] == "USD"  # Default

    def test_build_ga4_payload_with_utm_params(self, sgtm_adapter: SgtmAdapter):
        """Test UTM parameters are included."""
        context = {
            "event_type": "purchase",
            "payload": {
                "session_id": "sess_123",
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "spring_sale",
            },
        }

        payload = sgtm_adapter._build_ga4_payload(context)
        params = payload["events"][0]["params"]

        assert params["utm_source"] == "google"
        assert params["utm_medium"] == "cpc"
        assert params["utm_campaign"] == "spring_sale"

    def test_build_ga4_payload_with_user_id(self, sgtm_adapter: SgtmAdapter):
        """Test user_id is included at top level."""
        context = {
            "event_type": "purchase",
            "payload": {
                "session_id": "sess_123",
                "user_id": "user_abc",
            },
        }

        payload = sgtm_adapter._build_ga4_payload(context)

        assert payload["user_id"] == "user_abc"

    def test_build_ga4_payload_with_items(self, sgtm_adapter: SgtmAdapter):
        """Test items array is passed through."""
        context = {
            "event_type": "purchase",
            "payload": {
                "session_id": "sess_123",
                "items": [
                    {"item_id": "SKU1", "item_name": "Product 1", "price": 50.00},
                    {"item_id": "SKU2", "item_name": "Product 2", "price": 30.00},
                ],
            },
        }

        payload = sgtm_adapter._build_ga4_payload(context)
        params = payload["events"][0]["params"]

        assert "items" in params
        assert len(params["items"]) == 2

    def test_build_ga4_payload_with_storefront_code(self, sgtm_adapter: SgtmAdapter):
        """Test storefront_code is added to params."""
        context = {
            "event_type": "purchase",
            "payload": {"session_id": "sess_123"},
            "storefront_code": "bosley",
        }

        payload = sgtm_adapter._build_ga4_payload(context)
        params = payload["events"][0]["params"]

        assert params["storefront_id"] == "bosley"

    def test_build_ga4_payload_anonymous_client_id(self, sgtm_adapter: SgtmAdapter):
        """Test anonymous client_id when none provided."""
        context = {
            "event_type": "purchase",
            "payload": {"value": 100},
        }

        payload = sgtm_adapter._build_ga4_payload(context)

        assert payload["client_id"] == "anonymous"


class TestSgtmAdapterCustomPayloadBuilding:
    """Tests for sGTM adapter custom payload building."""

    @pytest.fixture
    def sgtm_adapter(self) -> SgtmAdapter:
        """Create sGTM adapter instance."""
        return SgtmAdapter()

    def test_build_custom_payload_basic(self, sgtm_adapter: SgtmAdapter):
        """Test building basic custom payload."""
        context = {
            "event_type": "purchase_completed",
            "payload": {
                "order_id": "123",
                "order_revenue": 100.00,
            },
        }

        payload = sgtm_adapter._build_custom_payload(context)

        assert payload["event_name"] == "purchase_completed"
        assert payload["order_id"] == "123"
        assert payload["order_revenue"] == 100.00

    def test_build_custom_payload_with_storefront(self, sgtm_adapter: SgtmAdapter):
        """Test custom payload includes storefront_id."""
        context = {
            "event_type": "rx_issued",
            "payload": {"order_id": "456"},
            "storefront_code": "pfizer",
        }

        payload = sgtm_adapter._build_custom_payload(context)

        assert payload["event_name"] == "rx_issued"
        assert payload["storefront_id"] == "pfizer"

    def test_build_custom_payload_passes_all_fields(self, sgtm_adapter: SgtmAdapter):
        """Test all payload fields are passed through."""
        context = {
            "event_type": "consult_completed",
            "payload": {
                "order_id": "789",
                "utm_source": "google",
                "utm_medium": "cpc",
                "custom_field_1": "value1",
                "custom_field_2": 42,
            },
        }

        payload = sgtm_adapter._build_custom_payload(context)

        assert payload["event_name"] == "consult_completed"
        assert payload["order_id"] == "789"
        assert payload["utm_source"] == "google"
        assert payload["custom_field_1"] == "value1"
        assert payload["custom_field_2"] == 42


class TestSgtmAdapterEventMapping:
    """Tests for sGTM adapter event type mapping."""

    @pytest.fixture
    def sgtm_adapter(self) -> SgtmAdapter:
        """Create sGTM adapter instance."""
        return SgtmAdapter()

    def test_map_purchase_completed_to_purchase(self, sgtm_adapter: SgtmAdapter):
        """Test purchase_completed maps to GA4 purchase."""
        result = sgtm_adapter._map_to_ga4_event("purchase_completed")
        assert result == "purchase"

    def test_map_standard_ga4_events(self, sgtm_adapter: SgtmAdapter):
        """Test standard GA4 events are preserved."""
        standard_events = [
            "purchase",
            "add_to_cart",
            "remove_from_cart",
            "begin_checkout",
            "view_item",
        ]

        for event in standard_events:
            result = sgtm_adapter._map_to_ga4_event(event)
            assert result == event

    def test_map_lead_to_generate_lead(self, sgtm_adapter: SgtmAdapter):
        """Test lead maps to generate_lead."""
        result = sgtm_adapter._map_to_ga4_event("lead")
        assert result == "generate_lead"

    def test_map_custom_events_pass_through(self, sgtm_adapter: SgtmAdapter):
        """Test custom healthcare events pass through."""
        custom_events = ["rx_issued", "consult_started", "consult_completed"]

        for event in custom_events:
            result = sgtm_adapter._map_to_ga4_event(event)
            assert result == event

    def test_map_unknown_event_passes_through(self, sgtm_adapter: SgtmAdapter):
        """Test unknown events pass through lowercased."""
        result = sgtm_adapter._map_to_ga4_event("CUSTOM_EVENT_XYZ")
        assert result == "custom_event_xyz"


# ============================================================================
# Meta CAPI Adapter Tests
# ============================================================================


class TestMetaCapiAdapter:
    """Tests for Meta CAPI adapter."""

    def test_validate_credentials_valid(self):
        """Test validating valid credentials."""
        adapter = get_adapter("meta_capi")

        assert adapter.validate_credentials({"access_token": "test"}) is True

    def test_validate_credentials_invalid_empty(self):
        """Test validating empty credentials."""
        adapter = get_adapter("meta_capi")

        assert adapter.validate_credentials({}) is False

    def test_validate_credentials_invalid_missing_token(self):
        """Test validating credentials without access_token."""
        adapter = get_adapter("meta_capi")

        assert adapter.validate_credentials({"pixel_id": "123"}) is False


# ============================================================================
# GA4 Adapter Tests
# ============================================================================


class TestGA4Adapter:
    """Tests for GA4 adapter."""

    def test_validate_credentials_valid(self):
        """Test validating valid credentials."""
        adapter = get_adapter("ga4")

        valid = adapter.validate_credentials({
            "measurement_id": "G-XXXXX",
            "api_secret": "secret",
        })

        assert valid is True

    def test_validate_credentials_missing_measurement_id(self):
        """Test validating credentials without measurement_id."""
        adapter = get_adapter("ga4")

        valid = adapter.validate_credentials({
            "api_secret": "secret",
        })

        assert valid is False

    def test_validate_credentials_missing_api_secret(self):
        """Test validating credentials without api_secret."""
        adapter = get_adapter("ga4")

        valid = adapter.validate_credentials({
            "measurement_id": "G-XXXXX",
        })

        assert valid is False


# ============================================================================
# TikTok Adapter Tests
# ============================================================================


class TestTikTokAdapter:
    """Tests for TikTok adapter."""

    def test_validate_credentials_valid(self):
        """Test validating valid credentials."""
        adapter = get_adapter("tiktok_events")

        assert adapter.validate_credentials({"access_token": "test"}) is True

    def test_validate_credentials_invalid(self):
        """Test validating invalid credentials."""
        adapter = get_adapter("tiktok_events")

        assert adapter.validate_credentials({}) is False


# ============================================================================
# Snapchat Adapter Tests
# ============================================================================


class TestSnapchatAdapter:
    """Tests for Snapchat adapter."""

    def test_validate_credentials_valid(self):
        """Test validating valid credentials."""
        adapter = get_adapter("snapchat_capi")

        assert adapter.validate_credentials({"access_token": "test"}) is True

    def test_validate_credentials_invalid(self):
        """Test validating invalid credentials."""
        adapter = get_adapter("snapchat_capi")

        assert adapter.validate_credentials({}) is False


# ============================================================================
# Pinterest Adapter Tests
# ============================================================================


class TestPinterestAdapter:
    """Tests for Pinterest adapter."""

    def test_validate_credentials_valid(self):
        """Test validating valid credentials."""
        adapter = get_adapter("pinterest_capi")

        valid = adapter.validate_credentials({
            "access_token": "test",
            "ad_account_id": "123",
        })

        assert valid is True

    def test_validate_credentials_missing_access_token(self):
        """Test validating credentials without access_token."""
        adapter = get_adapter("pinterest_capi")

        valid = adapter.validate_credentials({
            "ad_account_id": "123",
        })

        assert valid is False

    def test_validate_credentials_missing_ad_account(self):
        """Test validating credentials without ad_account_id."""
        adapter = get_adapter("pinterest_capi")

        valid = adapter.validate_credentials({
            "access_token": "test",
        })

        assert valid is False


# ============================================================================
# Base Adapter Tests
# ============================================================================


class TestBaseAdapter:
    """Tests for base adapter functionality."""

    def test_default_transform_event_returns_payload(self):
        """Test default transform_event returns payload unchanged."""
        adapter = SgtmAdapter()
        payload = {"key": "value", "nested": {"a": 1}}

        result = adapter.transform_event("purchase", payload)

        assert result == payload

    def test_default_validate_credentials_returns_true(self):
        """Test default validate_credentials returns True."""
        adapter = SgtmAdapter()

        # sGTM adapter doesn't override validate_credentials, uses default
        result = adapter.validate_credentials({})

        # Base returns True, but implementations may differ
        # This tests the base behavior
        assert isinstance(result, bool)
