import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_request_id,
    get_audit_service,
)
from app.services import AuditService
from app.services.exceptions import ResourceNotFoundError
from app.schemas import (
    ApiResponse,
    ApiCollectionResponse,
    ResponseMeta,
    PaginationMeta,
    AuditEventResponse,
    AuditEventType,
)

router = APIRouter()


def _to_audit_response(e) -> AuditEventResponse:
    """Convert AuditEvent ORM model to schema representation."""
    return AuditEventResponse(
        public_id=e.public_id,
        event_type=AuditEventType(e.event_type),
        actor_id=str(e.actor_id) if e.actor_id else None,
        entity_type=e.entity_type,
        entity_id=str(e.entity_id) if e.entity_id else None,
        request_id=e.request_id,
        run_id=e.run_id,
        payload=e.payload or {},
        created_at=e.created_at.isoformat() if e.created_at else "",
    )


@router.get(
    "/events",
    response_model=ApiCollectionResponse[AuditEventResponse],
    summary="Query append-only audit events",
)
def list_audit_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    request_id_filter: Optional[str] = Query(None, alias="request_id", description="Filter by X-Request-ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    request_id: str = Depends(get_request_id),
    audit_service: AuditService = Depends(get_audit_service),
) -> ApiCollectionResponse[AuditEventResponse]:
    """Query tamper-evident audit trail entries with pagination."""
    items, total = audit_service.audit_repo.list(
        event_type=event_type,
        entity_type=entity_type,
        request_id=request_id_filter,
        page=page,
        page_size=page_size,
    )
    responses = [_to_audit_response(e) for e in items]
    return ApiCollectionResponse(
        data=responses,
        meta=ResponseMeta(
            request_id=request_id,
            pagination=PaginationMeta(page=page, page_size=page_size, total=total),
        ),
    )


@router.get(
    "/events/{id}",
    response_model=ApiResponse[AuditEventResponse],
    summary="Get audit event by public ID",
)
def get_audit_event(
    id: str,
    request_id: str = Depends(get_request_id),
    audit_service: AuditService = Depends(get_audit_service),
) -> ApiResponse[AuditEventResponse]:
    """Retrieve details of a single immutable audit event."""
    event = audit_service.get_event(id)
    if not event:
        raise ResourceNotFoundError("AuditEvent", id)
    return ApiResponse(
        data=_to_audit_response(event),
        meta=ResponseMeta(request_id=request_id),
    )
