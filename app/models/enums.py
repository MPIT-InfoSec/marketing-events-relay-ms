"""Enum types for database models."""

from enum import Enum


class AuthType(str, Enum):
    """Authentication type for platform APIs."""

    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    ACCESS_TOKEN = "access_token"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"


class EventStatus(str, Enum):
    """Status of marketing events."""

    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class DestinationType(str, Enum):
    """Destination type for event delivery."""

    SGTM = "sgtm"
    DIRECT = "direct"


class AttemptStatus(str, Enum):
    """Status of individual delivery attempts."""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class SgtmClientType(str, Enum):
    """Type of sGTM client configuration.

    Determines how events are formatted and sent to sGTM.
    """

    GA4 = "ga4"  # GA4 Measurement Protocol format to /g/collect or /mp/collect
    CUSTOM = "custom"  # Custom JSON format to custom endpoint path
