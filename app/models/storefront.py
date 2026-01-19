"""Storefront model."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.credential import PlatformCredential
    from app.models.event import MarketingEvent
    from app.models.sgtm_config import StorefrontSgtmConfig


class Storefront(Base, TimestampMixin):
    """Storefront entity - represents a merchant/store."""

    __tablename__ = "storefronts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    storefront_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="External storefront identifier",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Storefront display name",
    )
    domain: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Primary domain for the storefront",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Kill switch - when False, no events processed",
    )

    # Relationships
    sgtm_config: Mapped[Optional["StorefrontSgtmConfig"]] = relationship(
        "StorefrontSgtmConfig",
        back_populates="storefront",
        uselist=False,
        cascade="all, delete-orphan",
    )
    credentials: Mapped[list["PlatformCredential"]] = relationship(
        "PlatformCredential",
        back_populates="storefront",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["MarketingEvent"]] = relationship(
        "MarketingEvent",
        back_populates="storefront",
        cascade="all, delete-orphan",
    )
