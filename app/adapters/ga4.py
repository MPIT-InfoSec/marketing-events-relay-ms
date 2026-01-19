"""Google Analytics 4 Measurement Protocol adapter."""

import logging
from typing import Any

import httpx

from app.adapters.base import AdapterResult, BaseAdapter
from app.adapters.factory import register_adapter
from app.core.config import settings
from app.models.enums import DestinationType

logger = logging.getLogger(__name__)


@register_adapter("ga4")
class GA4Adapter(BaseAdapter):
    """Adapter for GA4 Measurement Protocol."""

    platform_code = "ga4"
    BASE_URL = "https://www.google-analytics.com/mp/collect"

    async def send(self, context: dict[str, Any]) -> AdapterResult:
        """Send event to GA4 Measurement Protocol."""
        destination_type = context.get("destination_type")

        # If sGTM destination, route through sGTM
        if destination_type == DestinationType.SGTM:
            from app.adapters.sgtm import SgtmAdapter
            sgtm_adapter = SgtmAdapter()
            context["credentials"]["_platform_code"] = self.platform_code
            return await sgtm_adapter.send(context)

        # Direct API call
        return await self._send_direct(context)

    async def _send_direct(self, context: dict[str, Any]) -> AdapterResult:
        """Send event directly to GA4 Measurement Protocol."""
        credentials = context.get("credentials", {})
        measurement_id = credentials.get("measurement_id")
        api_secret = credentials.get("api_secret")

        if not measurement_id:
            return AdapterResult.error("Missing measurement_id in credentials")
        if not api_secret:
            return AdapterResult.error("Missing api_secret in credentials")

        # Build GA4 payload
        payload = self._build_payload(context)

        params = {
            "measurement_id": measurement_id,
            "api_secret": api_secret,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
                response = await client.post(
                    self.BASE_URL,
                    params=params,
                    json=payload,
                )

                # GA4 returns 204 on success with no body
                if response.status_code in (200, 204):
                    return AdapterResult.ok(
                        status_code=response.status_code,
                        response_body=response.text[:1000] if response.text else None,
                    )
                else:
                    return AdapterResult.error(
                        error_message=f"GA4 returned {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text[:1000],
                    )

        except httpx.TimeoutException:
            return AdapterResult.error("GA4 request timed out")
        except httpx.RequestError as e:
            return AdapterResult.error(f"GA4 request failed: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error sending to GA4")
            return AdapterResult.error(f"Unexpected error: {str(e)}")

    def _build_payload(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build GA4 Measurement Protocol payload."""
        event_type = context["event_type"]
        payload = context["payload"]

        # Map to GA4 event names
        event_name_map = {
            "purchase": "purchase",
            "add_to_cart": "add_to_cart",
            "begin_checkout": "begin_checkout",
            "add_payment_info": "add_payment_info",
            "view_item": "view_item",
            "search": "search",
            "lead": "generate_lead",
            "complete_registration": "sign_up",
            "subscribe": "subscribe",
        }

        ga4_event = event_name_map.get(event_type, event_type)

        # Build event params
        params = {}
        if "currency" in payload:
            params["currency"] = payload["currency"]
        if "value" in payload:
            params["value"] = float(payload["value"])
        if "transaction_id" in payload:
            params["transaction_id"] = payload["transaction_id"]

        # Items
        if "items" in payload:
            params["items"] = [
                {
                    "item_id": item.get("item_id", item.get("id")),
                    "item_name": item.get("item_name", item.get("name")),
                    "quantity": item.get("quantity", 1),
                    "price": item.get("price"),
                }
                for item in payload["items"]
            ]

        # Get client_id
        user_data = payload.get("user_data", {})
        client_id = payload.get("client_id") or user_data.get("client_id") or "anonymous"

        ga4_payload = {
            "client_id": client_id,
            "events": [
                {
                    "name": ga4_event,
                    "params": params,
                }
            ],
        }

        # Add user_id if available
        user_id = user_data.get("user_id")
        if user_id:
            ga4_payload["user_id"] = user_id

        return ga4_payload

    def validate_credentials(self, credentials: dict[str, Any]) -> bool:
        """Validate GA4 credentials."""
        return "measurement_id" in credentials and "api_secret" in credentials
