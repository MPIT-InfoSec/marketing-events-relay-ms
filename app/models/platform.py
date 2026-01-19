"""Ad Analytics Platform model."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import AuthType

if TYPE_CHECKING:
    from app.models.credential import PlatformCredential


class AdAnalyticsPlatform(Base, TimestampMixin):
    """Master list of supported ad analytics platforms."""

    __tablename__ = "ad_analytics_platforms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    platform_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique platform code (e.g., 'meta_capi', 'ga4')",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Platform display name",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="advertising",
        comment="Platform category (advertising, analytics, etc.)",
    )
    tier: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        index=True,
        comment="Priority tier: 1=critical, 2=important, 3=standard",
    )
    auth_type: Mapped[AuthType] = mapped_column(
        String(20),
        nullable=False,
        default=AuthType.ACCESS_TOKEN,
        comment="Authentication type required",
    )
    api_base_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Base URL for platform API",
    )
    credential_schema: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON schema for required credentials",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Platform description and notes",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Global kill switch for this platform",
    )

    # Relationships
    credentials: Mapped[list["PlatformCredential"]] = relationship(
        "PlatformCredential",
        back_populates="platform",
        cascade="all, delete-orphan",
    )
