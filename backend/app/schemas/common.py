from datetime import datetime, timezone
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

# Re-export standardized response models
from app.schemas.responses import (
    PaginationMeta,
    ResponseMeta,
    ApiResponse,
    ApiCollectionResponse,
    FieldErrorItem,
    ErrorBody,
    ApiErrorResponse,
)

T = TypeVar("T")


class MetaSchema(BaseModel):
    """Standard metadata envelope attached to successful responses."""

    request_id: str = Field(..., description="Unique request identifier")
    schema_version: str = Field(default="v1", description="API schema contract version")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of response generation",
    )


class DataEnvelope(BaseModel, Generic[T]):
    """Standard success response envelope for AllocateAI APIs."""

    data: T = Field(..., description="Response payload")
    meta: MetaSchema = Field(..., description="Response metadata")


class ErrorDetail(BaseModel):
    """Standard error detail object."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured error context or validation errors")
    request_id: str = Field(..., description="Unique request identifier associated with the error")


class ErrorEnvelope(BaseModel):
    """Standard error response envelope for AllocateAI APIs."""

    error: ErrorDetail = Field(..., description="Error payload")


def build_meta(request_id: str, schema_version: str = "v1") -> MetaSchema:
    """Build a standard metadata object."""
    return MetaSchema(
        request_id=request_id,
        schema_version=schema_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def build_envelope(data: Any, request_id: str, schema_version: str = "v1") -> Dict[str, Any]:
    """Helper to construct dictionary for standard data envelope."""
    return {
        "data": data,
        "meta": {
            "request_id": request_id,
            "schema_version": schema_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


def build_error_envelope(
    code: str,
    message: str,
    request_id: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Helper to construct dictionary for standard error envelope."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details if details is not None else {},
            "request_id": request_id,
        }
    }
