import uuid
from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_request_id,
    get_due_diligence_service,
    get_due_diligence_engine,
)
from app.services import (
    DueDiligenceService,
    DueDiligenceEngine,
)
from app.schemas import (
    ApiResponse,
    ResponseMeta,
    DueDiligenceReport,
    DueDiligenceCheck,
    DueDiligenceRisk,
    VerificationStatus,
)
from app.schemas.due_diligence import DEFAULT_DISCLAIMER

router = APIRouter()


def _to_due_diligence_report(r) -> DueDiligenceReport:
    """Helper to convert ORM model to Pydantic DueDiligenceReport schema."""
    checks = [
        DueDiligenceCheck(
            check_name=c.get("check_name", "compliance_check"),
            status=VerificationStatus(c.get("status", "VERIFIED")),
            source=c.get("source"),
            evidence=c.get("evidence"),
            confidence=float(c.get("confidence", 0.0)),
            checked_at=c.get("checked_at", "2026-09-03T12:00:00Z"),
        )
        for c in (r.checks or [])
    ]
    return DueDiligenceReport(
        report_id=r.public_id,
        ngo_id=str(r.ngo_id),
        overall_status=VerificationStatus(r.overall_status),
        risk_level=DueDiligenceRisk(r.risk_level),
        checks=checks,
        flags=r.flags or [],
        missing_documents=r.missing_documents or [],
        model_name=r.model_name,
        model_version=r.model_version or "due-diligence-v1",
        disclaimer=getattr(r, "disclaimer", DEFAULT_DISCLAIMER),
    )


@router.post(
    "/{ngo_id}/evaluate",
    response_model=ApiResponse[DueDiligenceReport],
    status_code=status.HTTP_201_CREATED,
    summary="Evaluate NGO regulatory and compliance due diligence",
)
def evaluate_ngo(
    ngo_id: uuid.UUID,
    request_id: str = Depends(get_request_id),
    dd_service: DueDiligenceService = Depends(get_due_diligence_service),
    engine: DueDiligenceEngine = Depends(get_due_diligence_engine),
) -> ApiResponse[DueDiligenceReport]:
    """Audit NGO compliance markers and generate evidence report."""
    report = dd_service.evaluate_ngo(
        ngo_id=ngo_id,
        engine=engine,
        request_id=request_id,
    )
    return ApiResponse(
        data=_to_due_diligence_report(report),
        meta=ResponseMeta(request_id=request_id),
    )


@router.get(
    "/{ngo_id}",
    response_model=ApiResponse[DueDiligenceReport],
    summary="Get latest due diligence report for an NGO",
)
def get_latest_report(
    ngo_id: uuid.UUID,
    request_id: str = Depends(get_request_id),
    dd_service: DueDiligenceService = Depends(get_due_diligence_service),
) -> ApiResponse[DueDiligenceReport]:
    """Retrieve the most recent due diligence findings and risk level for an NGO."""
    report = dd_service.get_latest_report(ngo_id=ngo_id)
    return ApiResponse(
        data=_to_due_diligence_report(report),
        meta=ResponseMeta(request_id=request_id),
    )
