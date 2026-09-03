import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.due_diligence_report import DueDiligenceReport
from app.repositories.base import BaseRepository


class DueDiligenceRepository(BaseRepository[DueDiligenceReport]):
    """Data access repository for DueDiligenceReport audit records."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, DueDiligenceReport)

    def create(
        self,
        public_id: str,
        ngo_id: uuid.UUID,
        overall_status: str,
        risk_level: str,
        checks: Dict[str, Any],
        flags: Optional[List[str]] = None,
        missing_documents: Optional[List[str]] = None,
        model_name: Optional[str] = None,
        model_version: str = "due-diligence-v1",
    ) -> DueDiligenceReport:
        """Create and persist a due diligence report."""
        report = DueDiligenceReport(
            public_id=public_id,
            ngo_id=ngo_id,
            overall_status=overall_status,
            risk_level=risk_level,
            checks=checks,
            flags=flags if flags is not None else [],
            missing_documents=missing_documents if missing_documents is not None else [],
            model_name=model_name,
            model_version=model_version,
        )
        return self.add(report, flush=True)

    def get_by_public_id(self, public_id: str) -> Optional[DueDiligenceReport]:
        """Fetch due diligence report by public ID (e.g. DD-0001)."""
        stmt = select(DueDiligenceReport).where(DueDiligenceReport.public_id == public_id)
        return self.session.scalar(stmt)

    def get_latest_for_ngo(self, ngo_id: uuid.UUID) -> Optional[DueDiligenceReport]:
        """Fetch the latest report generated for a specific NGO."""
        stmt = (
            select(DueDiligenceReport)
            .where(DueDiligenceReport.ngo_id == ngo_id)
            .order_by(DueDiligenceReport.created_at.desc(), DueDiligenceReport.id.asc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def list_by_ngo(self, ngo_id: uuid.UUID) -> List[DueDiligenceReport]:
        """List all due diligence reports for an NGO."""
        stmt = (
            select(DueDiligenceReport)
            .where(DueDiligenceReport.ngo_id == ngo_id)
            .order_by(DueDiligenceReport.created_at.desc(), DueDiligenceReport.id.asc())
        )
        return list(self.session.scalars(stmt).all())

    def update(
        self,
        report: DueDiligenceReport,
        overall_status: Optional[str] = None,
        risk_level: Optional[str] = None,
        checks: Optional[Dict[str, Any]] = None,
        flags: Optional[List[str]] = None,
        missing_documents: Optional[List[str]] = None,
    ) -> DueDiligenceReport:
        """Update review findings on a report."""
        if overall_status is not None:
            report.overall_status = overall_status
        if risk_level is not None:
            report.risk_level = risk_level
        if checks is not None:
            report.checks = checks
        if flags is not None:
            report.flags = flags
        if missing_documents is not None:
            report.missing_documents = missing_documents
        self.session.flush()
        return report
