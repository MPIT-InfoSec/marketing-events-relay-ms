"""Custom exceptions for the application."""

from typing import Any, Optional


class BaseAppException(Exception):
    """Base exception for all application exceptions."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(BaseAppException):
    """Resource not found."""

    def __init__(
        self,
        resource: str,
        identifier: Any,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            status_code=404,
            error_code="NOT_FOUND",
            details=details or {"resource": resource, "identifier": str(identifier)},
        )


class ConflictError(BaseAppException):
    """Resource conflict (duplicate, constraint violation)."""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details,
        )


class ValidationError(BaseAppException):
    """Validation error."""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationError(BaseAppException):
    """Authentication failed."""

    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_FAILED",
            details=details,
        )


class AuthorizationError(BaseAppException):
    """Authorization failed."""

    def __init__(
        self,
        message: str = "Access denied",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_FAILED",
            details=details,
        )


class EncryptionError(BaseAppException):
    """Encryption/decryption error."""

    def __init__(
        self,
        message: str = "Encryption operation failed",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="ENCRYPTION_ERROR",
            details=details,
        )


class ExternalServiceError(BaseAppException):
    """External service error (sGTM, platform APIs)."""

    def __init__(
        self,
        service: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"{service}: {message}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details or {"service": service},
        )


class RateLimitError(BaseAppException):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        _details = details or {}
        if retry_after:
            _details["retry_after"] = retry_after
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=_details,
        )


class KillSwitchError(BaseAppException):
    """Kill switch is active, preventing operation."""

    def __init__(
        self,
        resource: str,
        identifier: Any,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"{resource} '{identifier}' is disabled (kill switch active)",
            status_code=503,
            error_code="KILL_SWITCH_ACTIVE",
            details=details or {"resource": resource, "identifier": str(identifier)},
        )
