"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Marketing Events Relay"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = Field(
        default="mysql+aiomysql://root:password@localhost:3306/marketing_events_relay",
        description="Async MySQL connection URL",
    )
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=100)
    database_pool_recycle: int = Field(default=3600, ge=60)

    # Security
    basic_auth_username: str = Field(default="admin", min_length=3)
    basic_auth_password: str = Field(default="changeme", min_length=8)
    encryption_key: str = Field(
        default="",
        description="32-byte Fernet encryption key (base64 encoded)",
    )

    # Event Processing
    max_retry_attempts: int = Field(default=5, ge=1, le=10)
    retry_backoff_base: int = Field(default=60, ge=10)
    event_batch_size: int = Field(default=100, ge=1, le=1000)

    # HTTP Client
    http_timeout: int = Field(default=30, ge=5, le=120)
    http_max_connections: int = Field(default=100, ge=10, le=500)

    # Logging
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_format: str = "json"

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate that encryption key is properly formatted if provided."""
        if v and len(v) != 44:  # Base64 encoded 32-byte key
            raise ValueError("Encryption key must be a 44-character base64-encoded Fernet key")
        return v

    @property
    def sync_database_url(self) -> str:
        """Return synchronous database URL for Alembic."""
        return self.database_url.replace("aiomysql", "pymysql")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
