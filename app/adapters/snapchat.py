"""Snapchat Conversions API adapter."""

import hashlib
import logging
import time
from typing import Any

import httpx

from app.adapters.base import AdapterResult, BaseAdapter
from app.adapters.factory import register_adapter
from app.core.config import settings
from app.models.enums import DestinationType

logger = logging.getLogger(__name__)


@register_adapter("snapchat_capi")
class SnapchatAdapter(BaseAdapter):
    """Adapter for Snapchat Conversions API."""

    platform_code = "snapchat_capi"
    BASE_URL = "https://tr.snapchat.com/v2/conversion"

    async def send(self, context: dict[str, Any]) -> AdapterResult:
        """Send event to Snapchat Conversions API."""
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
        """Send event directly to Snapchat CAPI."""
        credentials = context.get("credentials", {})
        access_token = credentials.get("access_token")
        pixel_id = context.get("pixel_id") or credentials.get("pixel_id")

        if not access_token:
            return AdapterResult.error("Missing access_token in credentials")
        if not pixel_id:
            return AdapterResult.error("Missing pixel_id")

        # Build Snapchat event payload
        event_data = self._build_event(context, pixel_id)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
                response = await client.post(
                    self.BASE_URL,
                    headers=headers,
                    json=event_data,
                )

                if response.status_code in (200, 202):
                    return AdapterResult.ok(
                        status_code=response.status_code,
                        response_body=response.text[:1000],
                    )
                else:
                    return AdapterResult.error(
                        error_message=f"Snapchat CAPI returned {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text[:1000],
                    )

        except httpx.TimeoutException:
            return AdapterResult.error("Snapchat request timed out")
        except httpx.RequestError as e:
            return AdapterResult.error(f"Snapchat request failed: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error sending to Snapchat")
            return AdapterResult.error(f"Unexpected error: {str(e)}")

    def _build_event(
        self,
        context: dict[str, Any],
        pixel_id: str,
    ) -> dict[str, Any]:
        """Build Snapchat CAPI payload."""
        event_type = context["event_type"]
        payload = context["payload"]

        # Map to Snapchat event names
        event_name_map = {
            "purchase": "PURCHASE",
            "add_to_cart": "ADD_CART",
            "begin_checkout": "START_CHECKOUT",
            "add_payment_info": "ADD_BILLING",
            "view_item": "VIEW_CONTENT",
            "search": "SEARCH",
            "lead": "SIGN_UP",
            "complete_registration": "SIGN_UP",
            "subscribe": "SUBSCRIBE",
        }

        snap_event = event_name_map.get(event_type, event_type.upper())

        # Build event conversion
        event_conversion = {
            "event_type": snap_event,
            "event_conversion_type": "WEB",
            "timestamp": str(int(time.time() * 1000)),
            "pixel_id": pixel_id,
        }

        # Price data
        if "value" in payload:
            event_conversion["price"] = float(payload["value"])
        if "currency" in payload:
            event_conversion["currency"] = payload["currency"]
        if "transaction_id" in payload:
            event_conversion["transaction_id"] = payload["transaction_id"]

        # Item data
        if "items" in payload:
            event_conversion["item_ids"] = [
                item.get("item_id", item.get("id"))
                for item in payload["items"]
            ]
            event_conversion["number_items"] = sum(
                item.get("quantity", 1) for item in payload["items"]
            )

        # User data (hashed)
        user_data = payload.get("user_data", {})
        if user_data.get("email"):
            event_conversion["hashed_email"] = self._hash_value(user_data["email"])
        if user_data.get("phone"):
            event_conversion["hashed_phone_number"] = self._hash_value(user_data["phone"])
        if user_data.get("client_ip_address"):
            event_conversion["hashed_ip_address"] = self._hash_value(
                user_data["client_ip_address"]
            )

        return event_conversion

    def _hash_value(self, value: str) -> str:
        """Hash a value using SHA256."""
        return hashlib.sha256(value.lower().strip().encode()).hexdigest()

    def validate_credentials(self, credentials: dict[str, Any]) -> bool:
        """Validate Snapchat credentials."""
        return "access_token" in credentials
