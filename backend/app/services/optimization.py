import uuid
from decimal import Decimal
from typing import Optional, Tuple, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.optimization_run import OptimizationRun
from app.models.allocation import Allocation as AllocationModel
from app.repositories.optimization import OptimizationRepository
from app.repositories.allocation import AllocationRepository
from app.repositories.project import ProjectRepository
from app.repositories.impact_dna import ImpactDNARepository
from app.repositories.saturation import SaturationRepository
from app.services.audit import AuditService
from app.services.interfaces import OptimizationEngine
from app.services.exceptions import (
    ResourceNotFoundError,
    ServiceValidationError,
    ProcessingError,
)
from app.schemas.enums import OptimizationStatus, AuditEventType
from app.schemas.optimization import OptimizationRequest, OptimizationResult
from app.schemas.project import Project as SchemaProject
from app.schemas.geography import Geography
from app.schemas.beneficiary import BeneficiaryProfile
from app.schemas.financials import Financials
from app.schemas.impact_dna import ImpactDNA as SchemaImpactDNA
from app.schemas.saturation import SaturationResult as SchemaSaturationResult
from app.db.identifiers import generate_public_id


class OptimizationService:
    """Service orchestrating MILP portfolio optimization runs, allocation persistence, and audit logs."""

    def __init__(
        self,
        session: Session,
        optimization_repository: Optional[OptimizationRepository] = None,
        allocation_repository: Optional[AllocationRepository] = None,
        project_repository: Optional[ProjectRepository] = None,
        impact_dna_repository: Optional[ImpactDNARepository] = None,
        saturation_repository: Optional[SaturationRepository] = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        self.session = session
        self.opt_repo = optimization_repository or OptimizationRepository(session)
        self.alloc_repo = allocation_repository or AllocationRepository(session)
        self.project_repo = project_repository or ProjectRepository(session)
        self.dna_repo = impact_dna_repository or ImpactDNARepository(session)
        self.sat_repo = saturation_repository or SaturationRepository(session)
        self.audit_service = audit_service or AuditService(session)

    def create_optimization_run(
        self,
        request: OptimizationRequest,
        engine: OptimizationEngine,
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> OptimizationResult:
        """Atomically execute solver run, validate budget invariant, persist allocations, and log audit."""
        # 1. Verify all requested projects exist
        projects_orm = []
        schema_projects = []
        impact_dna_map: Dict[str, SchemaImpactDNA] = {}
        saturation_map: Dict[str, SchemaSaturationResult] = {}

        for pid in request.project_ids:
            proj = self.project_repo.get_by_public_id(pid)
            if not proj:
                raise ResourceNotFoundError("Project", pid)
            projects_orm.append(proj)

            # Build schema project representation for engine
            sp = SchemaProject(
                project_id=proj.public_id,
                name=proj.name,
                ngo_id=str(proj.ngo_id),
                sector=proj.sector,
                geographies=[Geography(state=g.state, district=g.district, block=g.block) for g in proj.geographies],
                beneficiary_profile=BeneficiaryProfile(target_count=1000),
                financials=Financials(
                    requested_amount_paise=proj.requested_amount,
                    current_funding_paise=proj.current_funding,
                ),
                duration_months=proj.duration_months,
            )
            schema_projects.append(sp)

            # Map DNA if exists
            if proj.impact_dna:
                d = proj.impact_dna
                impact_dna_map[pid] = SchemaImpactDNA(
                    dna_id=d.public_id,
                    project_id=pid,
                    need_score=float(d.need_score),
                    expected_impact_score=float(d.expected_impact_score),
                    cost_efficiency_score=float(d.cost_efficiency_score),
                    evidence_strength_score=float(d.evidence_strength_score),
                    scalability_score=float(d.scalability_score),
                    implementation_risk_score=float(d.implementation_risk_score),
                    beneficiary_reach=d.beneficiary_reach,
                    estimated_impact_per_lakh=float(d.estimated_impact_per_lakh),
                    extraction_confidence=float(d.extraction_confidence),
                    model_name=d.model_name,
                    prompt_version=d.prompt_version,
                )

            # Map Saturation if exists
            latest_sat = self.sat_repo.get_latest_for_project(proj.id)
            if latest_sat:
                saturation_map[pid] = SchemaSaturationResult(
                    project_id=pid,
                    state=latest_sat.state,
                    sector=latest_sat.sector,
                    saturation_index=float(latest_sat.saturation_index),
                    need_score=float(latest_sat.need_score),
                    existing_csr_amount_paise=latest_sat.existing_csr_amount,
                    estimated_beneficiary_coverage=float(latest_sat.beneficiary_coverage),
                    confidence=float(latest_sat.confidence),
                )

        # 2. Assign authoritative public ID
        stmt = select(func.count()).select_from(OptimizationRun)
        count = self.session.scalar(stmt) or 0
        run_public_id = generate_public_id("OPT", count + 1)

        input_snapshot = {
            "budget_paise": request.budget_paise,
            "project_ids": request.project_ids,
            "weights": request.weights.model_dump(),
            "constraints": request.constraints.model_dump(),
            "marginal_increment_paise": request.marginal_increment_paise,
        }

        # 3. Create initial RUNNING record
        run = self.opt_repo.create(
            public_id=run_public_id,
            budget_paise=request.budget_paise,
            weights=request.weights.model_dump(),
            constraints=request.constraints.model_dump(),
            calculation_versions={"solver": "scipy-milp-v1"},
            input_snapshot=input_snapshot,
            status=OptimizationStatus.RUNNING.value,
        )

        # 4. Audit execution start
        self.audit_service.record_event(
            event_type=AuditEventType.OPTIMIZATION_STARTED,
            payload={"run_id": run_public_id, "budget_paise": request.budget_paise, "project_count": len(request.project_ids)},
            entity_type="optimization_runs",
            entity_id=run.id,
            actor_id=actor_id,
            request_id=request_id,
            run_id=run_public_id,
        )

        try:
            # 5. Invoke solver engine
            try:
                opt_result = engine.optimize(
                    projects=schema_projects,
                    impact_dna_map=impact_dna_map,
                    saturation_map=saturation_map,
                    request=request,
                    run_id=run_public_id,
                )
            except Exception as e:
                run.status = OptimizationStatus.FAILED.value
                self.session.flush()
                self.audit_service.record_event(
                    event_type=AuditEventType.ERROR_OCCURRED,
                    payload={"run_id": run_public_id, "error": str(e)},
                    entity_type="optimization_runs",
                    entity_id=run.id,
                    actor_id=actor_id,
                    request_id=request_id,
                    run_id=run_public_id,
                )
                self.session.commit()
                raise ProcessingError(f"Optimization engine failure: {str(e)}", cause=e)

            # 6. Verify budget invariant: allocated + unallocated == budget
            if opt_result.allocated_paise + opt_result.unallocated_paise != opt_result.budget_paise:
                raise ServiceValidationError(
                    f"Budget invariant violated: {opt_result.allocated_paise} + "
                    f"{opt_result.unallocated_paise} != {opt_result.budget_paise}"
                )

            # Map project public ID to UUID
            proj_by_pub_id = {p.public_id: p for p in projects_orm}

            # 7. Persist allocations in bulk
            allocation_models = []
            for alloc_schema in opt_result.allocations:
                if alloc_schema.project_id not in proj_by_pub_id:
                    raise ServiceValidationError(
                        f"Allocation references unknown project ID '{alloc_schema.project_id}'"
                    )
                p_orm = proj_by_pub_id[alloc_schema.project_id]
                am = AllocationModel(
                    optimization_run_id=run.id,
                    project_id=p_orm.id,
                    allocated_amount=alloc_schema.allocated_amount_paise,
                    marginal_score=Decimal(str(round(alloc_schema.marginal_impact_score, 5))),
                    base_score=Decimal(str(round(alloc_schema.base_score, 5))),
                    saturation_index=Decimal(str(round(alloc_schema.saturation_index, 5))),
                    reason_codes={"codes": [rc.value for rc in alloc_schema.reason_codes]},
                    rank=alloc_schema.rank,
                    status=alloc_schema.status.value,
                )
                allocation_models.append(am)

            self.alloc_repo.bulk_create(allocation_models)

            # 8. Save result snapshot and seal as COMPLETED
            result_snapshot_data = opt_result.model_dump()
            self.opt_repo.save_result_snapshot(
                run=run,
                result_snapshot=result_snapshot_data,
                total_predicted_impact=Decimal(str(round(opt_result.total_predicted_impact, 4))),
                mark_completed=True,
            )

            # 9. Audit completion
            self.audit_service.record_event(
                event_type=AuditEventType.OPTIMIZATION_COMPLETED,
                payload={
                    "run_id": run_public_id,
                    "allocated_paise": opt_result.allocated_paise,
                    "unallocated_paise": opt_result.unallocated_paise,
                    "allocation_count": len(allocation_models),
                    "total_predicted_impact": opt_result.total_predicted_impact,
                },
                entity_type="optimization_runs",
                entity_id=run.id,
                actor_id=actor_id,
                request_id=request_id,
                run_id=run_public_id,
            )

            self.session.commit()
            return opt_result

        except Exception:
            self.session.rollback()
            raise

    def get_optimization_run(self, public_id: str) -> OptimizationRun:
        """Fetch optimization run by public ID or raise ResourceNotFoundError."""
        run = self.opt_repo.get_by_public_id(public_id)
        if not run:
            raise ResourceNotFoundError("OptimizationRun", public_id)
        return run

    def list_optimization_runs(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[OptimizationRun], int]:
        """List optimization runs with deterministic pagination."""
        return self.opt_repo.list(status=status, page=page, page_size=page_size)
