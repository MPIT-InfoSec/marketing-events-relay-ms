"""Initial schema - all 6 tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Storefronts table
    op.create_table(
        "storefronts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("storefront_id", sa.String(50), nullable=False, comment="External storefront identifier"),
        sa.Column("name", sa.String(255), nullable=False, comment="Storefront display name"),
        sa.Column("domain", sa.String(255), nullable=True, comment="Primary domain for the storefront"),
        sa.Column("description", sa.Text(), nullable=True, comment="Optional description"),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True, comment="Kill switch"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_storefronts_storefront_id", "storefronts", ["storefront_id"], unique=True)
    op.create_index("ix_storefronts_is_active", "storefronts", ["is_active"])

    # Storefront sGTM Config table
    # Supports two client types:
    #   - ga4: GA4 Measurement Protocol format to /g/collect or /mp/collect
    #   - custom: Flexible JSON format to custom endpoint path
    op.create_table(
        "storefront_sgtm_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("storefront_id", sa.Integer(), nullable=False),
        sa.Column("sgtm_url", sa.String(500), nullable=False, comment="sGTM container base URL"),
        sa.Column("client_type", sa.String(20), nullable=False, default="ga4", comment="Client type: ga4 or custom"),
        # GA4 Client fields
        sa.Column("container_id", sa.String(50), nullable=True, comment="GTM container ID (GTM-XXXXXX)"),
        sa.Column("measurement_id", sa.String(50), nullable=True, comment="GA4 Measurement ID (G-XXXXXX)"),
        sa.Column("api_secret", sa.Text(), nullable=True, comment="Encrypted API secret for GA4"),
        # Custom Client fields
        sa.Column("custom_endpoint_path", sa.String(100), nullable=True, default="/collect", comment="Endpoint path for custom client"),
        sa.Column("custom_headers", sa.Text(), nullable=True, comment="JSON custom headers for requests"),
        # Common fields
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True, comment="Kill switch for sGTM"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["storefront_id"], ["storefronts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_storefront_sgtm_config_storefront_id", "storefront_sgtm_config", ["storefront_id"], unique=True)
    op.create_index("ix_storefront_sgtm_config_is_active", "storefront_sgtm_config", ["is_active"])

    # Ad Analytics Platforms table
    op.create_table(
        "ad_analytics_platforms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("platform_code", sa.String(50), nullable=False, comment="Unique platform code"),
        sa.Column("name", sa.String(100), nullable=False, comment="Platform display name"),
        sa.Column("category", sa.String(50), nullable=False, default="advertising", comment="Platform category"),
        sa.Column("tier", sa.Integer(), nullable=False, default=3, comment="Priority tier: 1=critical, 2=important, 3=standard"),
        sa.Column("auth_type", sa.String(20), nullable=False, default="access_token", comment="Authentication type"),
        sa.Column("api_base_url", sa.String(500), nullable=True, comment="Base URL for platform API"),
        sa.Column("credential_schema", sa.Text(), nullable=True, comment="JSON schema for credentials"),
        sa.Column("description", sa.Text(), nullable=True, comment="Platform description"),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True, comment="Global kill switch"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ad_analytics_platforms_platform_code", "ad_analytics_platforms", ["platform_code"], unique=True)
    op.create_index("ix_ad_analytics_platforms_tier", "ad_analytics_platforms", ["tier"])
    op.create_index("ix_ad_analytics_platforms_is_active", "ad_analytics_platforms", ["is_active"])

    # Platform Credentials table
    op.create_table(
        "platform_credentials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("storefront_id", sa.Integer(), nullable=False),
        sa.Column("platform_id", sa.Integer(), nullable=False),
        sa.Column("credentials_encrypted", sa.Text(), nullable=False, comment="Fernet-encrypted JSON"),
        sa.Column("destination_type", sa.String(20), nullable=False, default="sgtm", comment="Delivery method"),
        sa.Column("pixel_id", sa.String(100), nullable=True, comment="Platform pixel ID"),
        sa.Column("account_id", sa.String(100), nullable=True, comment="Platform account ID"),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True, comment="Kill switch"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True, comment="Last successful use"),
        sa.Column("last_error", sa.Text(), nullable=True, comment="Last error message"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["storefront_id"], ["storefronts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["platform_id"], ["ad_analytics_platforms.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("storefront_id", "platform_id", name="uq_storefront_platform"),
    )
    op.create_index("ix_platform_credentials_storefront_id", "platform_credentials", ["storefront_id"])
    op.create_index("ix_platform_credentials_platform_id", "platform_credentials", ["platform_id"])
    op.create_index("ix_platform_credentials_is_active", "platform_credentials", ["is_active"])

    # Marketing Events table
    # Supports two ingestion paths:
    #   1. API Path: Uses storefront_id (integer FK, resolved by API from storefront_code)
    #   2. Direct DB Write: Can use storefront_id (integer) directly, or storefront_code (string) for worker resolution
    op.create_table(
        "marketing_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.String(100), nullable=False, comment="Unique event identifier (order_id from OMS)"),
        sa.Column("storefront_id", sa.Integer(), nullable=True, comment="FK to storefronts.id - set by API or direct write"),
        sa.Column("storefront_code", sa.String(50), nullable=True, comment="Storefront code for direct writes - worker resolves to storefront_id"),
        sa.Column("event_type", sa.String(50), nullable=False, comment="Event type (e.g., purchase_completed)"),
        sa.Column("event_payload", sa.Text(), nullable=False, comment="JSON event payload"),
        sa.Column("source_system", sa.String(50), nullable=False, default="oms", comment="Source: oms (API), oms_direct (DB write)"),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, default=0),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True, comment="Next retry timestamp"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True, comment="When fully processed"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="Last error message"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["storefront_id"], ["storefronts.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "storefront_id IS NOT NULL OR storefront_code IS NOT NULL",
            name="ck_marketing_events_storefront_required"
        ),
    )
    op.create_index("ix_marketing_events_event_id", "marketing_events", ["event_id"], unique=True)
    op.create_index("ix_marketing_events_storefront_id", "marketing_events", ["storefront_id"])
    op.create_index("ix_marketing_events_storefront_code", "marketing_events", ["storefront_code"])
    op.create_index("ix_marketing_events_event_type", "marketing_events", ["event_type"])
    op.create_index("ix_marketing_events_status", "marketing_events", ["status"])
    op.create_index("ix_marketing_events_next_retry_at", "marketing_events", ["next_retry_at"])

    # Event Attempts table
    op.create_table(
        "event_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("credential_id", sa.Integer(), nullable=False),
        sa.Column("destination_type", sa.String(20), nullable=False, comment="Delivery method"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("http_status_code", sa.Integer(), nullable=True, comment="HTTP response status"),
        sa.Column("response_body", sa.Text(), nullable=True, comment="Response body"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="Error message"),
        sa.Column("duration_ms", sa.Integer(), nullable=True, comment="Request duration ms"),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["event_id"], ["marketing_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["credential_id"], ["platform_credentials.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_event_attempts_event_id", "event_attempts", ["event_id"])
    op.create_index("ix_event_attempts_credential_id", "event_attempts", ["credential_id"])
    op.create_index("ix_event_attempts_status", "event_attempts", ["status"])
    op.create_index("ix_event_attempts_attempted_at", "event_attempts", ["attempted_at"])


def downgrade() -> None:
    op.drop_table("event_attempts")
    op.drop_table("marketing_events")
    op.drop_table("platform_credentials")
    op.drop_table("ad_analytics_platforms")
    op.drop_table("storefront_sgtm_config")
    op.drop_table("storefronts")
