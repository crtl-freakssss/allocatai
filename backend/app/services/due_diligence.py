import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.due_diligence_report import DueDiligenceReport as DueDiligenceReportModel
from app.repositories.due_diligence import DueDiligenceRepository
from app.repositories.ngo import NGORepository
from app.services.audit import AuditService
from app.services.interfaces import DueDiligenceEngine
from app.services.exceptions import (
    ResourceNotFoundError,
    ProcessingError,
)
from app.schemas.enums import AuditEventType
from app.schemas.due_diligence import DEFAULT_DISCLAIMER
from app.db.identifiers import generate_public_id


class DueDiligenceService:
    """Service orchestrating automated NGO due diligence assessments, evidence logging, and disclaimer integrity."""

    def __init__(
        self,
        session: Session,
        due_diligence_repository: Optional[DueDiligenceRepository] = None,
        ngo_repository: Optional[NGORepository] = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        self.session = session
        self.dd_repo = due_diligence_repository or DueDiligenceRepository(session)
        self.ngo_repo = ngo_repository or NGORepository(session)
        self.audit_service = audit_service or AuditService(session)

    def evaluate_ngo(
        self,
        ngo_id: uuid.UUID,
        engine: DueDiligenceEngine,
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> DueDiligenceReportModel:
        """Atomically invoke evaluation engine, verify compliance markers, and persist report with audit log."""
        ngo = self.ngo_repo.get_by_id(ngo_id)
        if not ngo:
            raise ResourceNotFoundError("NGO", ngo_id)

        stmt = select(func.count()).select_from(DueDiligenceReportModel)
        count = self.session.scalar(stmt) or 0
        report_public_id = generate_public_id("DD", count + 1)

        try:
            try:
                schema_report = engine.evaluate(
                    ngo_id=str(ngo.id),
                    name=ngo.name,
                    registration_number=ngo.registration_number,
                    report_id=report_public_id,
                )
            except Exception as e:
                raise ProcessingError(f"Due diligence engine failed: {str(e)}", cause=e)

            report = self.dd_repo.create(
                public_id=report_public_id,
                ngo_id=ngo.id,
                overall_status=schema_report.overall_status.value,
                risk_level=schema_report.risk_level.value,
                checks=[c.model_dump() for c in schema_report.checks],
                flags=schema_report.flags,
                missing_documents=schema_report.missing_documents,
                model_name=schema_report.model_name,
                model_version=schema_report.model_version,
            )

            self.audit_service.record_event(
                event_type=AuditEventType.DUE_DILIGENCE_COMPLETED,
                payload={
                    "report_id": report_public_id,
                    "ngo_id": str(ngo.id),
                    "overall_status": schema_report.overall_status.value,
                    "risk_level": schema_report.risk_level.value,
                },
                entity_type="due_diligence_reports",
                entity_id=report.id,
                actor_id=actor_id,
                request_id=request_id,
            )

            self.session.commit()
            report.disclaimer = DEFAULT_DISCLAIMER
            return report

        except Exception:
            self.session.rollback()
            raise

    def get_latest_report(self, ngo_id: uuid.UUID) -> DueDiligenceReportModel:
        """Fetch the latest due diligence assessment for an NGO or raise ResourceNotFoundError."""
        ngo = self.ngo_repo.get_by_id(ngo_id)
        if not ngo:
            raise ResourceNotFoundError("NGO", ngo_id)

        report = self.dd_repo.get_latest_for_ngo(ngo.id)
        if not report:
            raise ResourceNotFoundError("DueDiligenceReport", ngo_id)
        return report
