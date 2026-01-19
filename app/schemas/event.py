"""Event schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import AttemptStatus, DestinationType, EventStatus


class EventDataItem(BaseModel):
    """Schema for a single event in the data array from OMS."""

    t_value: Optional[str] = Field(default=None, alias="t-value", description="Tracking value")
    storefront_id: str = Field(description="Storefront identifier")
    event_name: str = Field(description="Event name/type")
    event_time: datetime = Field(description="Event timestamp")
    order_id: str = Field(description="Order ID (used as unique event identifier)")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    utm_source: Optional[str] = Field(default=None, description="UTM source")
    utm_medium: Optional[str] = Field(default=None, description="UTM medium")
    utm_campaign: Optional[str] = Field(default=None, description="UTM campaign")
    order_created_date: Optional[datetime] = Field(default=None, description="Order creation date")
    order_ship_date: Optional[datetime] = Field(default=None, description="Order ship date")
    order_revenue: Optional[float] = Field(default=None, description="Order revenue")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
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
        }

    def to_event_payload(self) -> dict[str, Any]:
        """Convert to event payload dict for storage."""
        payload = {
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "order_id": self.order_id,
        }
        if self.t_value:
            payload["t_value"] = self.t_value
        if self.session_id:
            payload["session_id"] = self.session_id
        if self.utm_source:
            payload["utm_source"] = self.utm_source
        if self.utm_medium:
            payload["utm_medium"] = self.utm_medium
        if self.utm_campaign:
            payload["utm_campaign"] = self.utm_campaign
        if self.order_created_date:
            payload["order_created_date"] = self.order_created_date.isoformat()
        if self.order_ship_date:
            payload["order_ship_date"] = self.order_ship_date.isoformat()
        if self.order_revenue is not None:
            payload["order_revenue"] = self.order_revenue
            payload["value"] = self.order_revenue  # For platform compatibility
        return payload


class EventBatchRequest(BaseModel):
    """Schema for batch event ingestion from OMS."""

    count: int = Field(description="Total count of events")
    data: list[EventDataItem] = Field(description="List of events")
    error: str = Field(default="", description="Error message if any")
    next_index: Optional[int] = Field(default=None, description="Next pagination index")
    next_url: Optional[str] = Field(default=None, description="Next pagination URL")
    previous_index: Optional[str] = Field(default=None, description="Previous pagination index")
    previous_url: Optional[str] = Field(default=None, description="Previous pagination URL")

    @model_validator(mode="after")
    def validate_data_not_empty(self) -> "EventBatchRequest":
        """Validate that data is not empty when no error."""
        if not self.error and len(self.data) == 0:
            raise ValueError("data cannot be empty when there is no error")
        return self

    class Config:
        json_schema_extra = {
            "example": {
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
                ],
                "error": "",
                "next_index": 1000,
                "next_url": "...",
                "previous_index": "",
                "previous_url": "",
            }
        }


# Legacy schema for backwards compatibility
class EventCreate(BaseModel):
    """Schema for a single event (legacy format)."""

    event_id: str = Field(min_length=1, max_length=100, description="Unique event identifier")
    event_type: str = Field(min_length=1, max_length=50, description="Event type")
    event_payload: dict[str, Any] = Field(description="Event data payload")
    source_system: str = Field(default="oms", max_length=50, description="Source system")

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate event type."""
        return v.lower()


class EventResponse(BaseModel):
    """Event response schema."""

    id: int
    event_id: str
    storefront_id: int
    event_type: str
    source_system: str
    status: EventStatus
    retry_count: int
    next_retry_at: Optional[datetime]
    processed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "event_id": "evt_123456",
                "storefront_id": 1,
                "event_type": "purchase",
                "source_system": "oms",
                "status": "delivered",
                "retry_count": 0,
                "next_retry_at": None,
                "processed_at": "2024-01-01T12:00:00Z",
                "error_message": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }


class EventAttemptResponse(BaseModel):
    """Event attempt response schema."""

    id: int
    event_id: int
    credential_id: int
    destination_type: DestinationType
    status: AttemptStatus
    http_status_code: Optional[int]
    error_message: Optional[str]
    duration_ms: Optional[int]
    attempted_at: datetime

    # Nested info
    platform_code: Optional[str] = None

    class Config:
        from_attributes = True


class EventWithAttemptsResponse(EventResponse):
    """Event response with delivery attempts."""

    attempts: list[EventAttemptResponse] = Field(default_factory=list)
    event_payload: dict[str, Any] = Field(description="Original event payload")

    class Config:
        from_attributes = True


class EventBatchResponse(BaseModel):
    """Response for batch event ingestion."""

    accepted: int = Field(description="Number of events accepted")
    rejected: int = Field(description="Number of events rejected")
    event_ids: list[str] = Field(description="IDs of accepted events")
    errors: list[dict[str, str]] = Field(default_factory=list, description="Rejection details")

    class Config:
        json_schema_extra = {
            "example": {
                "accepted": 5,
                "rejected": 1,
                "event_ids": ["evt_1", "evt_2", "evt_3", "evt_4", "evt_5"],
                "errors": [
                    {"event_id": "evt_dup", "error": "Event already exists"}
                ],
            }
        }
