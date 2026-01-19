"""Marketing Event model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import EventStatus

if TYPE_CHECKING:
    from app.models.event_attempt import EventAttempt
    from app.models.storefront import Storefront


class MarketingEvent(Base, TimestampMixin):
    """Incoming marketing event from OMS.

    Supports two ingestion paths:
    1. API Path: storefront_id is resolved from storefront_code by the API service
    2. Direct DB Write: Can use storefront_id (integer) directly, or storefront_code
       (string) which the worker will resolve before processing

    At least one of storefront_id or storefront_code must be provided.
    """

    __tablename__ = "marketing_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique event identifier (order_id from OMS)",
    )
    storefront_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("storefronts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="FK to storefronts.id - set by API or direct write",
    )
    storefront_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Storefront code for direct writes - worker resolves to storefront_id",
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Event type (e.g., purchase_completed, rx_issued)",
    )
    event_payload: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="JSON event payload",
    )
    source_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="oms",
        comment="Source system identifier",
    )
    status: Mapped[EventStatus] = mapped_column(
        String(20),
        nullable=False,
        default=EventStatus.PENDING,
        index=True,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Next retry timestamp for failed events",
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When event was fully processed",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Last error message if failed",
    )

    # Relationships
    storefront: Mapped["Storefront"] = relationship(
        "Storefront",
        back_populates="events",
    )
    attempts: Mapped[list["EventAttempt"]] = relationship(
        "EventAttempt",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventAttempt.attempted_at.desc()",
    )
