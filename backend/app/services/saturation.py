import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.models.saturation_result import SaturationResult as SaturationResultModel
from app.repositories.saturation import SaturationRepository
from app.repositories.project import ProjectRepository
from app.services.audit import AuditService
from app.services.interfaces import SaturationEngine
from app.services.exceptions import (
    ResourceNotFoundError,
    ServiceValidationError,
    ProcessingError,
)
from app.schemas.enums import AuditEventType


class SaturationService:
    """Service orchestrating regional saturation assessment calculation and auditing."""

    def __init__(
        self,
        session: Session,
        saturation_repository: Optional[SaturationRepository] = None,
        project_repository: Optional[ProjectRepository] = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        self.session = session
        self.sat_repo = saturation_repository or SaturationRepository(session)
        self.project_repo = project_repository or ProjectRepository(session)
        self.audit_service = audit_service or AuditService(session)

    def calculate_saturation(
        self,
        project_public_id: str,
        engine: SaturationEngine,
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> SaturationResultModel:
        """Atomically calculate saturation using engine and persist result with audit logging."""
        project = self.project_repo.get_by_public_id(project_public_id)
        if not project:
            raise ResourceNotFoundError("Project", project_public_id)

        if not project.geographies:
            raise ServiceValidationError(f"Project '{project_public_id}' has no assigned geographies", field="geographies")

        primary_state = project.geographies[0].state

        try:
            # Need score from DNA if exists, else default baseline
            need_score = 0.5
            if project.impact_dna:
                need_score = float(project.impact_dna.need_score)

            try:
                schema_sat = engine.calculate(
                    project_id=project_public_id,
                    state=primary_state,
                    sector=project.sector,
                    need_score=need_score,
                )
            except Exception as e:
                raise ProcessingError(f"Saturation engine failed: {str(e)}", cause=e)

            sat = self.sat_repo.create(
                project_id=project.id,
                state=primary_state,
                sector=project.sector,
                saturation_index=Decimal(str(round(schema_sat.saturation_index, 5))),
                need_score=Decimal(str(round(schema_sat.need_score, 5))),
                existing_csr_amount=schema_sat.existing_csr_amount_paise,
                beneficiary_coverage=Decimal(str(round(schema_sat.estimated_beneficiary_coverage, 5))),
                confidence=Decimal(str(round(schema_sat.confidence, 5))),
                calculation_version=schema_sat.calculation_version,
            )

            self.audit_service.record_event(
                event_type=AuditEventType.SATURATION_CALCULATED,
                payload={
                    "project_id": project_public_id,
                    "state": primary_state,
                    "saturation_index": float(schema_sat.saturation_index),
                },
                entity_type="saturation_results",
                entity_id=sat.id,
                actor_id=actor_id,
                request_id=request_id,
            )

            self.session.commit()
            return sat

        except Exception:
            self.session.rollback()
            raise

    def get_latest_saturation(self, project_public_id: str) -> SaturationResultModel:
        """Fetch the most recent saturation assessment for a project or raise ResourceNotFoundError."""
        project = self.project_repo.get_by_public_id(project_public_id)
        if not project:
            raise ResourceNotFoundError("Project", project_public_id)

        sat = self.sat_repo.get_latest_for_project(project.id)
        if not sat:
            raise ResourceNotFoundError("SaturationResult", project_public_id)
        return sat
