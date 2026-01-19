"""Event Attempt model for delivery audit log."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import AttemptStatus, DestinationType

if TYPE_CHECKING:
    from app.models.credential import PlatformCredential
    from app.models.event import MarketingEvent


class EventAttempt(Base):
    """Individual delivery attempt for an event."""

    __tablename__ = "event_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("marketing_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    credential_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("platform_credentials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    destination_type: Mapped[DestinationType] = mapped_column(
        String(20),
        nullable=False,
        comment="How event was delivered: sgtm or direct",
    )
    status: Mapped[AttemptStatus] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    http_status_code: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="HTTP response status code",
    )
    response_body: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Response body (truncated if large)",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if failed",
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Request duration in milliseconds",
    )
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    event: Mapped["MarketingEvent"] = relationship(
        "MarketingEvent",
        back_populates="attempts",
    )
    credential: Mapped["PlatformCredential"] = relationship(
        "PlatformCredential",
        back_populates="attempts",
    )
