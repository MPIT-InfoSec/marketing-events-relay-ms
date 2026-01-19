"""Base adapter interface for platform delivery."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AdapterResult:
    """Result of an adapter send operation."""

    success: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None

    @classmethod
    def ok(
        cls,
        status_code: int = 200,
        response_body: Optional[str] = None,
    ) -> "AdapterResult":
        """Create a successful result."""
        return cls(
            success=True,
            status_code=status_code,
            response_body=response_body,
        )

    @classmethod
    def error(
        cls,
        error_message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> "AdapterResult":
        """Create a failed result."""
        return cls(
            success=False,
            status_code=status_code,
            response_body=response_body,
            error_message=error_message,
        )


class BaseAdapter(ABC):
    """Base class for all platform adapters."""

    platform_code: str = "base"

    @abstractmethod
    async def send(self, context: dict[str, Any]) -> AdapterResult:
        """
        Send event to the platform.

        Args:
            context: Dictionary containing:
                - event_type: Type of event (purchase, add_to_cart, etc.)
                - payload: Event data payload
                - credentials: Decrypted platform credentials
                - pixel_id: Platform-specific pixel ID
                - account_id: Platform account ID
                - sgtm_config: sGTM config (if destination_type is sgtm)
                - destination_type: "sgtm" or "direct"

        Returns:
            AdapterResult with success/failure info
        """
        pass

    def transform_event(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Transform event payload to platform-specific format.

        Override in subclasses for platform-specific transformations.
        """
        return payload

    def validate_credentials(self, credentials: dict[str, Any]) -> bool:
        """
        Validate that required credentials are present.

        Override in subclasses to check platform-specific credentials.
        """
        return True
