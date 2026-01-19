"""Server-side Google Tag Manager adapter.

Supports two client types:
1. GA4 Client: Sends events in GA4 Measurement Protocol format to /mp/collect
2. Custom Client: Sends events as flexible JSON to configurable endpoint

GA4 Measurement Protocol format:
    POST https://sgtm-domain.com/mp/collect?measurement_id=G-XXX&api_secret=XXX
    {
        "client_id": "session_123",
        "events": [{
            "name": "purchase",
            "params": {"value": 80.79, "currency": "USD", ...}
        }]
    }

Custom format:
    POST https://sgtm-domain.com/collect
    {
        "event_name": "purchase_completed",
        "storefront_id": "bosley",
        "order_id": "123",
        "order_revenue": 80.79,
        ...all payload fields...
    }
"""

import json
import logging
from typing import Any

import httpx

from app.adapters.base import AdapterResult, BaseAdapter
from app.adapters.factory import register_adapter
from app.core.config import settings
from app.models.enums import SgtmClientType

logger = logging.getLogger(__name__)


@register_adapter("sgtm")
class SgtmAdapter(BaseAdapter):
    """Adapter for sending events to sGTM.

    Handles both GA4 Measurement Protocol and Custom HTTP client formats
    based on the sGTM configuration for the storefront.
    """

    platform_code = "sgtm"

    async def send(self, context: dict[str, Any]) -> AdapterResult:
        """Send event to sGTM endpoint.

        Args:
            context: Dict containing:
                - sgtm_config: StorefrontSgtmConfig object
                - event_type: Event type string (e.g., "purchase_completed")
                - payload: Dict of event data
                - storefront_code: Optional storefront identifier

        Returns:
            AdapterResult indicating success or failure
        """
        sgtm_config = context.get("sgtm_config")

        if not sgtm_config:
            return AdapterResult.error("No sGTM configuration found")

        if not sgtm_config.is_active:
            return AdapterResult.error("sGTM configuration is disabled")

        # Route to appropriate handler based on client type
        client_type = getattr(sgtm_config, "client_type", SgtmClientType.GA4)

        if client_type == SgtmClientType.CUSTOM:
            return await self._send_custom(sgtm_config, context)
        else:
            return await self._send_ga4(sgtm_config, context)

    async def _send_ga4(
        self,
        sgtm_config: Any,
        context: dict[str, Any],
    ) -> AdapterResult:
        """Send event using GA4 Measurement Protocol format.

        Endpoint: {sgtm_url}/mp/collect?measurement_id=G-XXX&api_secret=XXX
        """
        # Build GA4 Measurement Protocol payload
        payload = self._build_ga4_payload(context)

        # Build URL
        url = f"{sgtm_config.sgtm_url}/mp/collect"

        # Query params
        params = {}
        if sgtm_config.measurement_id:
            params["measurement_id"] = sgtm_config.measurement_id
        if sgtm_config.api_secret:
            params["api_secret"] = sgtm_config.api_secret

        headers = {"Content-Type": "application/json"}

        return await self._make_request(url, payload, headers, params)

    async def _send_custom(
        self,
        sgtm_config: Any,
        context: dict[str, Any],
    ) -> AdapterResult:
        """Send event using custom JSON format.

        Endpoint: {sgtm_url}{custom_endpoint_path}
        """
        # Build custom payload - pass through most fields
        payload = self._build_custom_payload(context)

        # Build URL with custom path
        endpoint_path = sgtm_config.custom_endpoint_path or "/collect"
        url = f"{sgtm_config.sgtm_url}{endpoint_path}"

        # Headers
        headers = {"Content-Type": "application/json"}

        # Add custom headers if configured
        if sgtm_config.custom_headers:
            try:
                custom_headers = (
                    json.loads(sgtm_config.custom_headers)
                    if isinstance(sgtm_config.custom_headers, str)
                    else sgtm_config.custom_headers
                )
                headers.update(custom_headers)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse custom_headers, ignoring")

        return await self._make_request(url, payload, headers)

    async def _make_request(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        params: dict[str, str] | None = None,
    ) -> AdapterResult:
        """Make HTTP request to sGTM."""
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    params=params or {},
                )

                if response.status_code in (200, 201, 202, 204):
                    return AdapterResult.ok(
                        status_code=response.status_code,
                        response_body=response.text[:1000] if response.text else "",
                    )
                else:
                    return AdapterResult.error(
                        error_message=f"sGTM returned {response.status_code}: {response.text[:500]}",
                        status_code=response.status_code,
                        response_body=response.text[:1000] if response.text else "",
                    )

        except httpx.TimeoutException:
            return AdapterResult.error("sGTM request timed out")
        except httpx.RequestError as e:
            return AdapterResult.error(f"sGTM request failed: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error sending to sGTM")
            return AdapterResult.error(f"Unexpected error: {str(e)}")

    def _build_ga4_payload(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build GA4 Measurement Protocol payload.

        Format:
        {
            "client_id": "...",
            "events": [{
                "name": "purchase",
                "params": {...}
            }]
        }
        """
        event_type = context["event_type"]
        payload = context["payload"]

        # Map custom event types to GA4 standard events where applicable
        ga4_event_name = self._map_to_ga4_event(event_type)

        # Extract or generate client_id
        client_id = (
            payload.get("client_id")
            or payload.get("session_id")
            or payload.get("user_data", {}).get("client_id")
            or "anonymous"
        )

        # Build event params
        event_params = self._build_ga4_params(event_type, payload, context)

        ga4_payload: dict[str, Any] = {
            "client_id": str(client_id),
            "events": [
                {
                    "name": ga4_event_name,
                    "params": event_params,
                }
            ],
        }

        # Add user_id if available (for cross-device tracking)
        user_id = payload.get("user_id") or payload.get("user_data", {}).get("user_id")
        if user_id:
            ga4_payload["user_id"] = str(user_id)

        return ga4_payload

    def _build_ga4_params(
        self,
        event_type: str,
        payload: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Build GA4 event params from payload."""
        params: dict[str, Any] = {}

        # Standard e-commerce params (GA4 names)
        if "currency" in payload:
            params["currency"] = payload["currency"]
        elif "order_revenue" in payload:
            params["currency"] = "USD"  # Default

        if "value" in payload:
            params["value"] = float(payload["value"])
        elif "order_revenue" in payload:
            params["value"] = float(payload["order_revenue"])

        if "transaction_id" in payload:
            params["transaction_id"] = payload["transaction_id"]
        elif "order_id" in payload:
            params["transaction_id"] = payload["order_id"]

        # Items array (for e-commerce)
        if "items" in payload:
            params["items"] = payload["items"]

        # UTM parameters (GA4 supports these in params)
        for utm_field in ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"]:
            if utm_field in payload:
                # GA4 uses traffic_source for some, but params work too
                params[utm_field] = payload[utm_field]

        # Add storefront identifier for sGTM routing
        storefront_code = context.get("storefront_code") or payload.get("storefront_id")
        if storefront_code:
            params["storefront_id"] = storefront_code

        # Add custom params (t-value, etc.)
        if "t_value" in payload:
            params["t_value"] = payload["t_value"]

        # Pass through other custom fields (excluding already mapped ones)
        exclude_keys = {
            "currency", "value", "transaction_id", "items", "user_data",
            "client_id", "session_id", "user_id", "order_revenue", "order_id",
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "storefront_id", "event_time", "t_value",
        }
        for key, val in payload.items():
            if key not in exclude_keys and not key.startswith("_"):
                params[key] = val

        return params

    def _build_custom_payload(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build custom JSON payload for sGTM custom client.

        Passes through all event data with minimal transformation.
        sGTM custom client will parse this based on its configuration.
        """
        event_type = context["event_type"]
        payload = context["payload"]
        storefront_code = context.get("storefront_code")

        # Start with event identification
        custom_payload: dict[str, Any] = {
            "event_name": event_type,
        }

        # Add storefront if available
        if storefront_code:
            custom_payload["storefront_id"] = storefront_code

        # Pass through all payload fields
        for key, value in payload.items():
            if key not in custom_payload:  # Don't overwrite event_name
                custom_payload[key] = value

        return custom_payload

    def _map_to_ga4_event(self, event_type: str) -> str:
        """Map custom event types to GA4 standard event names.

        GA4 has recommended event names for e-commerce:
        https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference/events
        """
        # Mapping from our event types to GA4 standard events
        ga4_event_map = {
            # E-commerce events
            "purchase": "purchase",
            "purchase_completed": "purchase",
            "add_to_cart": "add_to_cart",
            "remove_from_cart": "remove_from_cart",
            "begin_checkout": "begin_checkout",
            "add_payment_info": "add_payment_info",
            "add_shipping_info": "add_shipping_info",
            "view_item": "view_item",
            "view_item_list": "view_item_list",
            "select_item": "select_item",
            "view_cart": "view_cart",
            # Lead/conversion events
            "lead": "generate_lead",
            "generate_lead": "generate_lead",
            "sign_up": "sign_up",
            "complete_registration": "sign_up",
            "login": "login",
            # Custom healthcare/pharma events (pass through as custom)
            "rx_issued": "rx_issued",
            "consult_started": "consult_started",
            "consult_completed": "consult_completed",
            # Search/engagement
            "search": "search",
            "share": "share",
            # Other
            "subscribe": "subscribe",
            "refund": "refund",
        }

        # Return mapped name or original (GA4 accepts custom event names)
        return ga4_event_map.get(event_type.lower(), event_type.lower())
