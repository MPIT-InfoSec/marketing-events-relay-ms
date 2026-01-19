"""Storefront sGTM Configuration model."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import SgtmClientType

if TYPE_CHECKING:
    from app.models.storefront import Storefront


class StorefrontSgtmConfig(Base, TimestampMixin):
    """Server-side Google Tag Manager configuration for a storefront.

    Supports two client types:
    - GA4: Uses GA4 Measurement Protocol format, sends to /g/collect or /mp/collect
    - Custom: Uses custom JSON format, sends to configurable endpoint path

    For GA4 client type:
    - measurement_id and api_secret are typically required
    - Events are formatted as GA4 Measurement Protocol

    For Custom client type:
    - custom_endpoint_path defines where to POST (e.g., /collect, /events)
    - custom_event_key defines the JSON key for event name (default: "event_name")
    - Events are sent as flexible JSON matching your sGTM custom client
    """

    __tablename__ = "storefront_sgtm_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    storefront_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("storefronts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    sgtm_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="sGTM container base URL (e.g., https://tags.upscript.com)",
    )
    client_type: Mapped[SgtmClientType] = mapped_column(
        String(20),
        nullable=False,
        default=SgtmClientType.GA4,
        comment="Client type: ga4 (Measurement Protocol) or custom (flexible JSON)",
    )

    # GA4 Client fields
    container_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="GTM container ID (GTM-XXXXXX)",
    )
    measurement_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="GA4 Measurement ID (G-XXXXXX) - required for GA4 client",
    )
    api_secret: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Encrypted API secret for GA4 Measurement Protocol",
    )

    # Custom Client fields
    custom_endpoint_path: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="/collect",
        comment="Endpoint path for custom client (e.g., /collect, /events)",
    )
    custom_headers: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON string of custom headers to include in requests",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Kill switch for sGTM integration",
    )

    # Relationship
    storefront: Mapped["Storefront"] = relationship(
        "Storefront",
        back_populates="sgtm_config",
    )
