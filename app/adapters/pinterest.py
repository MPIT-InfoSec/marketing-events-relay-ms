"""Pinterest Conversions API adapter."""

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


@register_adapter("pinterest_capi")
class PinterestAdapter(BaseAdapter):
    """Adapter for Pinterest Conversions API."""

    platform_code = "pinterest_capi"
    BASE_URL = "https://api.pinterest.com/v5/ad_accounts"

    async def send(self, context: dict[str, Any]) -> AdapterResult:
        """Send event to Pinterest Conversions API."""
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
        """Send event directly to Pinterest CAPI."""
        credentials = context.get("credentials", {})
        access_token = credentials.get("access_token")
        ad_account_id = context.get("account_id") or credentials.get("ad_account_id")

        if not access_token:
            return AdapterResult.error("Missing access_token in credentials")
        if not ad_account_id:
            return AdapterResult.error("Missing ad_account_id")

        # Build Pinterest event payload
        event_data = self._build_event(context)

        url = f"{self.BASE_URL}/{ad_account_id}/events"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json={"data": [event_data]},
                )

                if response.status_code in (200, 202):
                    return AdapterResult.ok(
                        status_code=response.status_code,
                        response_body=response.text[:1000],
                    )
                else:
                    return AdapterResult.error(
                        error_message=f"Pinterest CAPI returned {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text[:1000],
                    )

        except httpx.TimeoutException:
            return AdapterResult.error("Pinterest request timed out")
        except httpx.RequestError as e:
            return AdapterResult.error(f"Pinterest request failed: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error sending to Pinterest")
            return AdapterResult.error(f"Unexpected error: {str(e)}")

    def _build_event(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build Pinterest CAPI payload."""
        event_type = context["event_type"]
        payload = context["payload"]

        # Map to Pinterest event names
        event_name_map = {
            "purchase": "checkout",
            "add_to_cart": "add_to_cart",
            "begin_checkout": "checkout",
            "add_payment_info": "checkout",
            "view_item": "page_visit",
            "search": "search",
            "lead": "lead",
            "complete_registration": "signup",
            "subscribe": "signup",
        }

        pinterest_event = event_name_map.get(event_type, "custom")

        # Build event data
        event_data = {
            "event_name": pinterest_event,
            "action_source": "web",
            "event_time": int(time.time()),
            "event_id": payload.get("transaction_id", str(int(time.time() * 1000))),
        }

        # Custom data
        custom_data = {}
        if "currency" in payload:
            custom_data["currency"] = payload["currency"]
        if "value" in payload:
            custom_data["value"] = str(float(payload["value"]))
        if "transaction_id" in payload:
            custom_data["order_id"] = payload["transaction_id"]

        # Contents
        if "items" in payload:
            custom_data["contents"] = [
                {
                    "id": item.get("item_id", item.get("id")),
                    "item_name": item.get("item_name", item.get("name")),
                    "quantity": item.get("quantity", 1),
                    "item_price": str(item.get("price", 0)),
                }
                for item in payload["items"]
            ]
            custom_data["num_items"] = sum(
                item.get("quantity", 1) for item in payload["items"]
            )

        if custom_data:
            event_data["custom_data"] = custom_data

        # User data (hashed)
        user_data = payload.get("user_data", {})
        user_info = {}

        if user_data.get("email"):
            user_info["em"] = [self._hash_value(user_data["email"])]
        if user_data.get("phone"):
            user_info["ph"] = [self._hash_value(user_data["phone"])]
        if user_data.get("first_name"):
            user_info["fn"] = [self._hash_value(user_data["first_name"])]
        if user_data.get("last_name"):
            user_info["ln"] = [self._hash_value(user_data["last_name"])]
        if user_data.get("city"):
            user_info["ct"] = [self._hash_value(user_data["city"])]
        if user_data.get("state"):
            user_info["st"] = [self._hash_value(user_data["state"])]
        if user_data.get("zip"):
            user_info["zp"] = [self._hash_value(user_data["zip"])]
        if user_data.get("country"):
            user_info["country"] = [self._hash_value(user_data["country"])]
        if user_data.get("external_id"):
            user_info["external_id"] = [self._hash_value(user_data["external_id"])]

        if user_info:
            event_data["user_data"] = user_info

        return event_data

    def _hash_value(self, value: str) -> str:
        """Hash a value using SHA256."""
        return hashlib.sha256(value.lower().strip().encode()).hexdigest()

    def validate_credentials(self, credentials: dict[str, Any]) -> bool:
        """Validate Pinterest credentials."""
        return "access_token" in credentials and "ad_account_id" in credentials
