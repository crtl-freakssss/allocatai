import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.impact_dna import ImpactDNA as ImpactDNAModel
from app.repositories.impact_dna import ImpactDNARepository
from app.repositories.project import ProjectRepository
from app.services.audit import AuditService
from app.services.interfaces import ImpactDNAEngine
from app.services.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    ProcessingError,
)
from app.schemas.enums import AuditEventType
from app.db.identifiers import generate_public_id


class ImpactDNAService:
    """Service orchestrating Impact DNA score generation, 1-to-1 binding, and auditing."""

    def __init__(
        self,
        session: Session,
        impact_dna_repository: Optional[ImpactDNARepository] = None,
        project_repository: Optional[ProjectRepository] = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        self.session = session
        self.dna_repo = impact_dna_repository or ImpactDNARepository(session)
        self.project_repo = project_repository or ProjectRepository(session)
        self.audit_service = audit_service or AuditService(session)

    def generate_dna(
        self,
        project_public_id: str,
        engine: ImpactDNAEngine,
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> ImpactDNAModel:
        """Atomically invoke ImpactDNA engine, assign authoritative DNA ID, and persist scores."""
        project = self.project_repo.get_by_public_id(project_public_id)
        if not project:
            raise ResourceNotFoundError("Project", project_public_id)

        existing = self.dna_repo.get_by_project_id(project.id)
        if existing:
            raise ResourceAlreadyExistsError("ImpactDNA", "project_id", project_public_id)

        try:
            geos = [{"state": g.state, "district": g.district, "block": g.block} for g in project.geographies]
            try:
                schema_dna = engine.generate(
                    project_id=project_public_id,
                    name=project.name,
                    sector=project.sector,
                    requested_amount_paise=project.requested_amount,
                    geographies=geos,
                )
            except Exception as e:
                raise ProcessingError(f"Impact DNA engine failed: {str(e)}", cause=e)

            stmt = select(func.count()).select_from(ImpactDNAModel)
            count = self.session.scalar(stmt) or 0
            public_id = generate_public_id("DNA", count + 1)

            dna = self.dna_repo.create(
                public_id=public_id,
                project_id=project.id,
                need_score=Decimal(str(round(schema_dna.need_score, 5))),
                expected_impact_score=Decimal(str(round(schema_dna.expected_impact_score, 5))),
                cost_efficiency_score=Decimal(str(round(schema_dna.cost_efficiency_score, 5))),
                evidence_strength_score=Decimal(str(round(schema_dna.evidence_strength_score, 5))),
                scalability_score=Decimal(str(round(schema_dna.scalability_score, 5))),
                implementation_risk_score=Decimal(str(round(schema_dna.implementation_risk_score, 5))),
                beneficiary_reach=schema_dna.beneficiary_reach,
                estimated_impact_per_lakh=Decimal(str(round(schema_dna.estimated_impact_per_lakh, 4))),
                missing_fields={"missing": schema_dna.missing_fields},
                extraction_confidence=Decimal(str(round(schema_dna.extraction_confidence, 5))),
                model_name=schema_dna.model_name,
                prompt_version=schema_dna.prompt_version,
                schema_version=schema_dna.schema_version,
            )

            self.audit_service.record_event(
                event_type=AuditEventType.IMPACT_DNA_CREATED,
                payload={
                    "public_id": public_id,
                    "project_id": project_public_id,
                    "expected_impact_score": float(schema_dna.expected_impact_score),
                },
                entity_type="impact_dna",
                entity_id=dna.id,
                actor_id=actor_id,
                request_id=request_id,
            )

            self.session.commit()
            return dna

        except Exception:
            self.session.rollback()
            raise

    def get_dna(self, project_public_id: str) -> ImpactDNAModel:
        """Fetch ImpactDNA for a project or raise ResourceNotFoundError."""
        project = self.project_repo.get_by_public_id(project_public_id)
        if not project:
            raise ResourceNotFoundError("Project", project_public_id)

        dna = self.dna_repo.get_by_project_id(project.id)
        if not dna:
            raise ResourceNotFoundError("ImpactDNA", project_public_id)
        return dna
