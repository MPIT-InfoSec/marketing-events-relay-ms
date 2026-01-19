"""Common schemas for pagination and error responses."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum records to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int = Field(description="Total number of records")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum records returned")
    has_more: bool = Field(description="Whether more records exist")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        skip: int,
        limit: int,
    ) -> "PaginatedResponse[T]":
        """Create paginated response."""
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total,
        )


class ErrorDetail(BaseModel):
    """Error detail."""

    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    error_code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(default=None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "NOT_FOUND",
                "message": "Storefront with identifier '123' not found",
                "details": {"resource": "Storefront", "identifier": "123"},
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Health status: healthy or unhealthy")
    version: str = Field(description="Application version")
    environment: str = Field(description="Current environment")


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str = Field(description="Ready status")
    database: str = Field(description="Database connection status")
