from typing import Any
from pydantic import BaseModel, Field
from app.schemas.enums import AuditEventType


class AuditEventCreate(BaseModel):
    """Payload to record an append-only audit event."""

    event_type: AuditEventType = Field(..., description="Classification category of event")
    actor_id: str | None = Field(default=None, description="Initiating user or service account ID")
    entity_type: str | None = Field(default=None, description="Affected resource table or domain type")
    entity_id: str | None = Field(default=None, description="Identifier of affected entity")
    request_id: str | None = Field(default=None, description="HTTP X-Request-ID for distributed tracing")
    run_id: str | None = Field(default=None, description="Associated solver run public ID, e.g. OPT-0001")
    payload: dict[str, Any] = Field(default_factory=dict, description="Structured event metadata or delta")


class AuditEventResponse(BaseModel):
    """API representation of an audit event log entry."""

    public_id: str = Field(..., description="Public identifier, e.g. AUD-0001")
    event_type: AuditEventType = Field(..., description="Classification category of event")
    actor_id: str | None = Field(default=None, description="Initiating user or service account ID")
    entity_type: str | None = Field(default=None, description="Affected resource table or domain type")
    entity_id: str | None = Field(default=None, description="Identifier of affected entity")
    request_id: str | None = Field(default=None, description="HTTP X-Request-ID for distributed tracing")
    run_id: str | None = Field(default=None, description="Associated solver run public ID, e.g. OPT-0001")
    payload: dict[str, Any] = Field(default_factory=dict, description="Structured event metadata")
    created_at: str = Field(..., description="UTC ISO timestamp of event occurrence")
