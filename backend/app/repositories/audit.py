import uuid
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.audit_event import AuditEvent
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditEvent]):
    """Append-only audit trail repository.

    Strict Contract Rules:
    - No updates allowed.
    - No deletes allowed.
    - Events are strictly append-only.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(session, AuditEvent)

    def create(
        self,
        public_id: str,
        event_type: str,
        payload: Dict[str, Any],
        actor_id: Optional[uuid.UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> AuditEvent:
        """Append a new audit event to the immutable audit trail."""
        event = AuditEvent(
            public_id=public_id,
            event_type=event_type,
            payload=payload,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            request_id=request_id,
            run_id=run_id,
        )
        return self.add(event, flush=True)

    def bulk_create(self, events: List[AuditEvent]) -> List[AuditEvent]:
        """Append multiple audit events in batch."""
        for ev in events:
            self.session.add(ev)
        self.session.flush()
        return events

    def get_by_public_id(self, public_id: str) -> Optional[AuditEvent]:
        """Fetch audit record by public ID (e.g. AUD-0001)."""
        stmt = select(AuditEvent).where(AuditEvent.public_id == public_id)
        return self.session.scalar(stmt)

    def list(
        self,
        event_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
        run_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AuditEvent], int]:
        """List audit events with deterministic pagination and search filters."""
        offset = max(0, (page - 1) * page_size)

        filters = []
        if event_type is not None:
            filters.append(AuditEvent.event_type == event_type)
        if entity_type is not None:
            filters.append(AuditEvent.entity_type == entity_type)
        if entity_id is not None:
            filters.append(AuditEvent.entity_id == entity_id)
        if actor_id is not None:
            filters.append(AuditEvent.actor_id == actor_id)
        if request_id is not None:
            filters.append(AuditEvent.request_id == request_id)
        if run_id is not None:
            filters.append(AuditEvent.run_id == run_id)

        total_stmt = select(func.count()).select_from(AuditEvent)
        if filters:
            total_stmt = total_stmt.where(*filters)
        total = self.session.scalar(total_stmt) or 0

        stmt = select(AuditEvent)
        if filters:
            stmt = stmt.where(*filters)

        stmt = stmt.order_by(AuditEvent.created_at.desc(), AuditEvent.id.asc()).offset(offset).limit(page_size)
        items = list(self.session.scalars(stmt).all())
        return items, total

    # Explicit enforcement of append-only guarantee:
    def update(self, *args: Any, **kwargs: Any) -> None:
        """Explicitly blocked: Audit logs are append-only and cannot be updated."""
        raise NotImplementedError("Audit events are strictly append-only and cannot be modified")

    def delete(self, *args: Any, **kwargs: Any) -> None:
        """Explicitly blocked: Audit logs are append-only and cannot be deleted."""
        raise NotImplementedError("Audit events are strictly append-only and cannot be deleted")
