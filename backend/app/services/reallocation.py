import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.reallocation_run import ReallocationRun
from app.repositories.reallocation import ReallocationRepository
from app.repositories.optimization import OptimizationRepository
from app.repositories.allocation import AllocationRepository
from app.repositories.project import ProjectRepository
from app.services.audit import AuditService
from app.services.interfaces import ReallocationEngine
from app.services.exceptions import (
    ResourceNotFoundError,
    InvalidStateTransitionError,
    ProcessingError,
)
from app.schemas.enums import OptimizationStatus, AuditEventType
from app.schemas.reallocation import ReallocationRequest, ReallocationResult
from app.schemas.allocation import Allocation as SchemaAllocation
from app.db.identifiers import generate_public_id


class ReallocationService:
    """Service orchestrating mid-cycle capital reallocation and auditing."""

    def __init__(
        self,
        session: Session,
        reallocation_repository: Optional[ReallocationRepository] = None,
        optimization_repository: Optional[OptimizationRepository] = None,
        allocation_repository: Optional[AllocationRepository] = None,
        project_repository: Optional[ProjectRepository] = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        self.session = session
        self.realloc_repo = reallocation_repository or ReallocationRepository(session)
        self.opt_repo = optimization_repository or OptimizationRepository(session)
        self.alloc_repo = allocation_repository or AllocationRepository(session)
        self.project_repo = project_repository or ProjectRepository(session)
        self.audit_service = audit_service or AuditService(session)

    def create_reallocation_run(
        self,
        request: ReallocationRequest,
        engine: ReallocationEngine,
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> ReallocationResult:
        """Atomically execute mid-cycle reallocation engine and persist result with audit log."""
        # 1. Verify previous optimization run exists and is COMPLETED
        prev_run = self.opt_repo.get_by_public_id(request.previous_run_id)
        if not prev_run:
            raise ResourceNotFoundError("OptimizationRun", request.previous_run_id)

        if prev_run.status != OptimizationStatus.COMPLETED.value:
            raise InvalidStateTransitionError(
                entity_type="OptimizationRun",
                current_state=prev_run.status,
                target_state="COMPLETED",
                message=f"Previous run '{request.previous_run_id}' is not in COMPLETED state",
            )

        # 2. Verify all performance update projects exist
        for u in request.performance_updates:
            if not self.project_repo.exists_by_public_id(u.project_id):
                raise ResourceNotFoundError("Project", u.project_id)

        # 3. Load previous allocations
        prev_alloc_models = self.alloc_repo.list_by_optimization_run(prev_run.id)
        schema_prev_allocations = []
        for am in prev_alloc_models:
            schema_prev_allocations.append(
                SchemaAllocation(
                    project_id=am.project.public_id,
                    allocated_amount_paise=am.allocated_amount,
                    marginal_impact_score=float(am.marginal_score) if am.marginal_score else 0.0,
                    base_score=float(am.base_score) if am.base_score else 0.0,
                    saturation_index=float(am.saturation_index) if am.saturation_index else 0.0,
                    reason_codes=am.reason_codes.get("codes", []),
                    rank=am.rank,
                    status=am.status,
                )
            )

        # 4. Generate authoritative REA ID
        stmt = select(func.count()).select_from(ReallocationRun)
        count = self.session.scalar(stmt) or 0
        realloc_pub_id = generate_public_id("REA", count + 1)

        try:
            # 5. Invoke engine
            try:
                realloc_result = engine.reallocate(
                    previous_run_id=request.previous_run_id,
                    previous_allocations=schema_prev_allocations,
                    performance_updates=request.performance_updates,
                    request=request,
                    realloc_run_id=realloc_pub_id,
                )
            except Exception as e:
                raise ProcessingError(f"Reallocation engine failed: {str(e)}", cause=e)

            # 6. Persist reallocation run
            realloc = self.realloc_repo.create(
                public_id=realloc_pub_id,
                previous_optimization_id=prev_run.id,
                budget_paise=request.budget_paise,
                performance_snapshot=[u.model_dump() for u in request.performance_updates],
                calculation_versions=realloc_result.calculation_versions,
                result_snapshot=realloc_result.model_dump(),
            )

            # 7. Audit event
            self.audit_service.record_event(
                event_type=AuditEventType.REALLOCATION_COMPLETED,
                payload={
                    "run_id": realloc_pub_id,
                    "previous_run_id": request.previous_run_id,
                    "total_budget_shifted_paise": realloc_result.total_budget_shifted_paise,
                    "changed_projects": realloc_result.changed_projects,
                },
                entity_type="reallocation_runs",
                entity_id=realloc.id,
                actor_id=actor_id,
                request_id=request_id,
                run_id=realloc_pub_id,
            )

            self.session.commit()
            return realloc_result

        except Exception:
            self.session.rollback()
            raise

    def get_reallocation_run(self, public_id: str) -> ReallocationRun:
        """Fetch reallocation run by public ID or raise ResourceNotFoundError."""
        run = self.realloc_repo.get_by_public_id(public_id)
        if not run:
            raise ResourceNotFoundError("ReallocationRun", public_id)
        return run
