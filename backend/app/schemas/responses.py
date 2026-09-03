from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata for collection endpoints."""

    page: int = Field(default=1, ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, description="Number of items per page")
    total: int = Field(..., ge=0, description="Total count of items across all pages")


class ResponseMeta(BaseModel):
    """Standardized metadata envelope attached to API responses."""

    request_id: str = Field(..., description="Unique request identifier, e.g. REQ-123 or req_abc")
    schema_version: str = Field(default="api-v1", description="API contract schema version")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of response generation",
    )
    pagination: PaginationMeta | None = Field(
        default=None,
        description="Pagination metadata when returning collections",
    )


class ApiResponse(BaseModel, Generic[T]):
    """Standard single-entity success envelope."""

    data: T = Field(..., description="Response payload")
    meta: ResponseMeta = Field(..., description="Response metadata")


class ApiCollectionResponse(BaseModel, Generic[T]):
    """Standard collection success envelope with pagination support."""

    data: list[T] = Field(..., description="List of response items")
    meta: ResponseMeta = Field(..., description="Response metadata with pagination")


class FieldErrorItem(BaseModel):
    """Individual field validation error detail."""

    field: str = Field(..., description="Name of the invalid field or path")
    reason: str = Field(..., description="Explanation of validation failure")


class ErrorBody(BaseModel):
    """Structured error payload without stack traces or secret leakage."""

    code: str = Field(..., description="Machine-readable error category, e.g. VALIDATION_ERROR")
    message: str = Field(..., description="Human-readable error description")
    details: Any = Field(default_factory=list, description="List of field errors or context dictionary")
    request_id: str = Field(..., description="Unique request identifier associated with error")


class ApiErrorResponse(BaseModel):
    """Standard error response envelope for AllocateAI APIs."""

    error: ErrorBody = Field(..., description="Standardized error body")
