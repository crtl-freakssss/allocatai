import uuid
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.audit_event import AuditEvent
from app.repositories.audit import AuditRepository
from app.db.identifiers import generate_public_id
from app.schemas.enums import AuditEventType


class AuditService:
    """Service for orchestrating append-only audit trail records."""

    def __init__(
        self,
        session: Session,
        audit_repository: Optional[AuditRepository] = None,
    ) -> None:
        self.session = session
        self.audit_repo = audit_repository or AuditRepository(session)

    def record_event(
        self,
        event_type: Union[AuditEventType, str],
        payload: Dict[str, Any],
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_id: Optional[str] = None,
    ) -> AuditEvent:
        """Append a tamper-evident audit record to the event store."""
        ev_type_str = event_type.value if isinstance(event_type, AuditEventType) else str(event_type)

        if not public_id:
            # Determine next sequence counter for deterministic AUD identifier
            stmt = select(func.count()).select_from(AuditEvent)
            count = self.session.scalar(stmt) or 0
            public_id = generate_public_id("AUD", count + 1)

        event = self.audit_repo.create(
            public_id=public_id,
            event_type=ev_type_str,
            payload=payload,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            request_id=request_id,
            run_id=run_id,
        )
        return event

    def get_event(self, public_id: str) -> Optional[AuditEvent]:
        """Fetch audit record by public identifier."""
        return self.audit_repo.get_by_public_id(public_id)
