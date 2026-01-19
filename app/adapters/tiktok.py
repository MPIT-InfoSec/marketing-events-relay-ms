"""TikTok Events API adapter."""

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


@register_adapter("tiktok_events")
class TikTokAdapter(BaseAdapter):
    """Adapter for TikTok Events API."""

    platform_code = "tiktok_events"
    BASE_URL = "https://business-api.tiktok.com/open_api/v1.3/pixel/track"

    async def send(self, context: dict[str, Any]) -> AdapterResult:
        """Send event to TikTok Events API."""
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
        """Send event directly to TikTok Events API."""
        credentials = context.get("credentials", {})
        access_token = credentials.get("access_token")
        pixel_code = context.get("pixel_id") or credentials.get("pixel_code")

        if not access_token:
            return AdapterResult.error("Missing access_token in credentials")
        if not pixel_code:
            return AdapterResult.error("Missing pixel_code")

        # Build TikTok event payload
        event_data = self._build_event(context, pixel_code)

        headers = {
            "Access-Token": access_token,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
                response = await client.post(
                    self.BASE_URL,
                    headers=headers,
                    json=event_data,
                )

                response_json = response.json() if response.text else {}

                # TikTok returns code 0 on success
                if response.status_code == 200 and response_json.get("code") == 0:
                    return AdapterResult.ok(
                        status_code=response.status_code,
                        response_body=response.text[:1000],
                    )
                else:
                    error_msg = response_json.get("message", f"Status {response.status_code}")
                    return AdapterResult.error(
                        error_message=f"TikTok API error: {error_msg}",
                        status_code=response.status_code,
                        response_body=response.text[:1000],
                    )

        except httpx.TimeoutException:
            return AdapterResult.error("TikTok request timed out")
        except httpx.RequestError as e:
            return AdapterResult.error(f"TikTok request failed: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error sending to TikTok")
            return AdapterResult.error(f"Unexpected error: {str(e)}")

    def _build_event(
        self,
        context: dict[str, Any],
        pixel_code: str,
    ) -> dict[str, Any]:
        """Build TikTok Events API payload."""
        event_type = context["event_type"]
        payload = context["payload"]

        # Map to TikTok event names
        event_name_map = {
            "purchase": "CompletePayment",
            "add_to_cart": "AddToCart",
            "begin_checkout": "InitiateCheckout",
            "add_payment_info": "AddPaymentInfo",
            "view_item": "ViewContent",
            "search": "Search",
            "lead": "SubmitForm",
            "complete_registration": "CompleteRegistration",
            "subscribe": "Subscribe",
        }

        tiktok_event = event_name_map.get(event_type, event_type)

        # Build properties
        properties = {}
        if "currency" in payload:
            properties["currency"] = payload["currency"]
        if "value" in payload:
            properties["value"] = float(payload["value"])
        if "transaction_id" in payload:
            properties["order_id"] = payload["transaction_id"]

        # Contents
        if "items" in payload:
            properties["contents"] = [
                {
                    "content_id": item.get("item_id", item.get("id")),
                    "content_name": item.get("item_name", item.get("name")),
                    "quantity": item.get("quantity", 1),
                    "price": item.get("price"),
                }
                for item in payload["items"]
            ]

        # User data
        user_data = payload.get("user_data", {})
        user = {}

        if user_data.get("email"):
            user["email"] = self._hash_value(user_data["email"])
        if user_data.get("phone"):
            user["phone"] = self._hash_value(user_data["phone"])
        if user_data.get("external_id"):
            user["external_id"] = self._hash_value(user_data["external_id"])

        # Build final payload
        tiktok_payload = {
            "pixel_code": pixel_code,
            "event": tiktok_event,
            "event_id": payload.get("transaction_id", str(int(time.time() * 1000))),
            "timestamp": str(int(time.time())),
            "properties": properties,
        }

        if user:
            tiktok_payload["user"] = user

        return tiktok_payload

    def _hash_value(self, value: str) -> str:
        """Hash a value using SHA256."""
        return hashlib.sha256(value.lower().strip().encode()).hexdigest()

    def validate_credentials(self, credentials: dict[str, Any]) -> bool:
        """Validate TikTok credentials."""
        return "access_token" in credentials
