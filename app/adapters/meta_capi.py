"""Meta Conversions API adapter."""

import hashlib
import json
import logging
import time
from typing import Any

import httpx

from app.adapters.base import AdapterResult, BaseAdapter
from app.adapters.factory import register_adapter
from app.core.config import settings
from app.models.enums import DestinationType

logger = logging.getLogger(__name__)


@register_adapter("meta_capi")
class MetaCapiAdapter(BaseAdapter):
    """Adapter for Meta Conversions API (Facebook/Instagram)."""

    platform_code = "meta_capi"
    API_VERSION = "v18.0"
    BASE_URL = "https://graph.facebook.com"

    async def send(self, context: dict[str, Any]) -> AdapterResult:
        """Send event to Meta Conversions API."""
        destination_type = context.get("destination_type")

        # If sGTM destination, route through sGTM
        if destination_type == DestinationType.SGTM:
            from app.adapters.sgtm import SgtmAdapter
            sgtm_adapter = SgtmAdapter()
            # Add platform identifier for sGTM routing
            context["credentials"]["_platform_code"] = self.platform_code
            return await sgtm_adapter.send(context)

        # Direct API call
        return await self._send_direct(context)

    async def _send_direct(self, context: dict[str, Any]) -> AdapterResult:
        """Send event directly to Meta CAPI."""
        credentials = context.get("credentials", {})
        access_token = credentials.get("access_token")
        pixel_id = context.get("pixel_id") or credentials.get("pixel_id")

        if not access_token:
            return AdapterResult.error("Missing access_token in credentials")
        if not pixel_id:
            return AdapterResult.error("Missing pixel_id")

        # Build Meta event payload
        event_data = self._build_event(context)

        url = f"{self.BASE_URL}/{self.API_VERSION}/{pixel_id}/events"
        params = {"access_token": access_token}

        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
                response = await client.post(
                    url,
                    params=params,
                    json={"data": [event_data]},
                )

                if response.status_code == 200:
                    return AdapterResult.ok(
                        status_code=response.status_code,
                        response_body=response.text[:1000],
                    )
                else:
                    return AdapterResult.error(
                        error_message=f"Meta CAPI returned {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text[:1000],
                    )

        except httpx.TimeoutException:
            return AdapterResult.error("Meta CAPI request timed out")
        except httpx.RequestError as e:
            return AdapterResult.error(f"Meta CAPI request failed: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error sending to Meta CAPI")
            return AdapterResult.error(f"Unexpected error: {str(e)}")

    def _build_event(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build Meta CAPI event payload."""
        event_type = context["event_type"]
        payload = context["payload"]

        # Map to Meta event names
        event_name_map = {
            "purchase": "Purchase",
            "add_to_cart": "AddToCart",
            "begin_checkout": "InitiateCheckout",
            "add_payment_info": "AddPaymentInfo",
            "view_item": "ViewContent",
            "search": "Search",
            "lead": "Lead",
            "complete_registration": "CompleteRegistration",
            "subscribe": "Subscribe",
        }

        event = {
            "event_name": event_name_map.get(event_type, event_type),
            "event_time": int(time.time()),
            "action_source": "website",
        }

        # User data (hashed)
        user_data = payload.get("user_data", {})
        if user_data:
            event["user_data"] = self._hash_user_data(user_data)

        # Custom data
        custom_data = {}
        if "currency" in payload:
            custom_data["currency"] = payload["currency"]
        if "value" in payload:
            custom_data["value"] = float(payload["value"])
        if "transaction_id" in payload:
            event["event_id"] = payload["transaction_id"]

        # Items/contents
        if "items" in payload:
            custom_data["contents"] = [
                {
                    "id": item.get("item_id", item.get("id")),
                    "quantity": item.get("quantity", 1),
                    "item_price": item.get("price"),
                }
                for item in payload["items"]
            ]
            custom_data["num_items"] = sum(
                item.get("quantity", 1) for item in payload["items"]
            )

        if custom_data:
            event["custom_data"] = custom_data

        return event

    def _hash_user_data(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """Hash user data for Meta CAPI (SHA256, lowercase, trimmed)."""
        hashed = {}

        hash_fields = ["email", "phone", "first_name", "last_name", "city", "state", "zip", "country"]

        for field in hash_fields:
            if field in user_data and user_data[field]:
                value = str(user_data[field]).lower().strip()
                hashed[self._get_meta_field_name(field)] = hashlib.sha256(
                    value.encode()
                ).hexdigest()

        # Pass through non-PII fields
        if "client_ip_address" in user_data:
            hashed["client_ip_address"] = user_data["client_ip_address"]
        if "client_user_agent" in user_data:
            hashed["client_user_agent"] = user_data["client_user_agent"]
        if "fbc" in user_data:
            hashed["fbc"] = user_data["fbc"]
        if "fbp" in user_data:
            hashed["fbp"] = user_data["fbp"]

        return hashed

    def _get_meta_field_name(self, field: str) -> str:
        """Map field names to Meta CAPI field names."""
        mapping = {
            "email": "em",
            "phone": "ph",
            "first_name": "fn",
            "last_name": "ln",
            "city": "ct",
            "state": "st",
            "zip": "zp",
            "country": "country",
        }
        return mapping.get(field, field)

    def validate_credentials(self, credentials: dict[str, Any]) -> bool:
        """Validate Meta CAPI credentials."""
        return "access_token" in credentials
