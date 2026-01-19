"""Platform Credential model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import DestinationType

if TYPE_CHECKING:
    from app.models.event_attempt import EventAttempt
    from app.models.platform import AdAnalyticsPlatform
    from app.models.storefront import Storefront


class PlatformCredential(Base, TimestampMixin):
    """Encrypted credentials for a storefront's platform integration."""

    __tablename__ = "platform_credentials"
    __table_args__ = (
        UniqueConstraint(
            "storefront_id",
            "platform_id",
            name="uq_storefront_platform",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    storefront_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("storefronts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ad_analytics_platforms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    credentials_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Fernet-encrypted JSON credentials",
    )
    destination_type: Mapped[DestinationType] = mapped_column(
        String(20),
        nullable=False,
        default=DestinationType.SGTM,
        comment="Delivery method: sgtm or direct",
    )
    pixel_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Platform-specific pixel/tracking ID",
    )
    account_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Platform account/advertiser ID",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Kill switch for this credential",
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful use timestamp",
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Last error message if any",
    )

    # Relationships
    storefront: Mapped["Storefront"] = relationship(
        "Storefront",
        back_populates="credentials",
    )
    platform: Mapped["AdAnalyticsPlatform"] = relationship(
        "AdAnalyticsPlatform",
        back_populates="credentials",
    )
    attempts: Mapped[list["EventAttempt"]] = relationship(
        "EventAttempt",
        back_populates="credential",
        cascade="all, delete-orphan",
    )
