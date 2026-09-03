"""Deterministic engine test doubles for Phase 4 service testing.

These test doubles return valid Phase 2 contract schemas without external network
or LLM dependencies.
"""

from typing import List, Dict, Optional, Any
from app.schemas import (
    ExtractionResult,
    Project,
    Geography,
    BeneficiaryProfile,
    Financials,
    ImpactMetric,
    EvidenceItem,
    ImpactDNA,
    SaturationResult,
    OptimizationRequest,
    OptimizationResult,
    Allocation,
    ReallocationRequest,
    ReallocationResult,
    DueDiligenceReport,
    DueDiligenceCheck,
    ProjectSector,
    ProposalStatus,
    VerificationStatus,
    DueDiligenceRisk,
    OptimizationStatus,
    AllocationStatus,
    ReasonCode,
)


class FakeExtractionEngine:
    """Deterministic double for ExtractionEngine."""

    def __init__(self, should_fail: bool = False, missing_fields: Optional[List[str]] = None) -> None:
        self.should_fail = should_fail
        self.missing_fields = missing_fields or []

    def extract(
        self,
        proposal_id: str,
        document_id: str,
        filename: str,
        mime_type: str,
        storage_key: str,
    ) -> ExtractionResult:
        if self.should_fail:
            raise RuntimeError("Fake extraction engine deliberate failure")

        extracted_proj = Project(
            project_id="ENGINE-GEN-001",  # Engine ID to be overridden by backend
            name="Community Water Purification",
            ngo_id="NGO-TEMP",
            sector=ProjectSector.ENVIRONMENT,
            geographies=[Geography(state="Rajasthan", district="Barmer", block="Sedwa")],
            beneficiary_profile=BeneficiaryProfile(target_count=2500, groups=["rural_households"]),
            financials=Financials(requested_amount_paise=500000000),  # ₹50 Lakhs
            duration_months=12,
            impact_metrics=[
                ImpactMetric(metric_id="MET-01", name="Clean water liters/day", unit="liters", target=10000.0)
            ],
            description="Extracted water purification project",
        )

        evidence = [
            EvidenceItem(
                evidence_id="EVD-01",
                source_type="PDF_TABLE",
                source_reference="Page 4, Table 2",
                claim="2500 households lack potability",
                extracted_value="2500",
                confidence=0.95,
                verification_status=VerificationStatus.UNVERIFIED,
            )
        ]

        return ExtractionResult(
            proposal_id=proposal_id,
            document_id=document_id,
            extracted_project=extracted_proj,
            evidence=evidence,
            missing_fields=self.missing_fields,
            warnings=[],
            extraction_confidence=0.92,
            model_name="fake-gemini-pro",
            prompt_version="fake-v1.0",
        )


class FakeImpactDNAEngine:
    """Deterministic double for ImpactDNAEngine."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def generate(
        self,
        project_id: str,
        name: str,
        sector: str,
        requested_amount_paise: int,
        geographies: List[Dict[str, Any]],
        beneficiary_profile: Optional[Dict[str, Any]] = None,
    ) -> ImpactDNA:
        if self.should_fail:
            raise RuntimeError("Fake DNA engine deliberate failure")

        return ImpactDNA(
            dna_id="DNA-ENGINE-STUB",
            project_id=project_id,
            need_score=0.88,
            expected_impact_score=0.91,
            cost_efficiency_score=0.84,
            evidence_strength_score=0.79,
            scalability_score=0.82,
            implementation_risk_score=0.15,
            beneficiary_reach=5000,
            estimated_impact_per_lakh=42.5,
            missing_fields=[],
            extraction_confidence=0.95,
            model_name="fake-dna-model",
            prompt_version="v1.0",
        )


class FakeSaturationEngine:
    """Deterministic double for SaturationEngine."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def calculate(
        self,
        project_id: str,
        state: str,
        sector: str,
        need_score: float,
    ) -> SaturationResult:
        if self.should_fail:
            raise RuntimeError("Fake saturation engine deliberate failure")

        return SaturationResult(
            project_id=project_id,
            state=state,
            sector=ProjectSector(sector) if sector in ProjectSector.__members__ else ProjectSector.OTHER,
            saturation_index=0.32,
            need_score=need_score,
            existing_csr_amount_paise=1000000000,
            estimated_beneficiary_coverage=0.35,
            confidence=0.90,
            calculation_version="fake-sat-v1",
        )


class FakeOptimizationEngine:
    """Deterministic double for OptimizationEngine."""

    def __init__(self, should_fail: bool = False, violate_budget: bool = False) -> None:
        self.should_fail = should_fail
        self.violate_budget = violate_budget

    def optimize(
        self,
        projects: List[Project],
        impact_dna_map: Dict[str, ImpactDNA],
        saturation_map: Dict[str, SaturationResult],
        request: OptimizationRequest,
        run_id: str,
    ) -> OptimizationResult:
        if self.should_fail:
            raise RuntimeError("Fake optimization solver deliberate failure")

        budget = request.budget_paise

        if self.violate_budget:
            # Deliberately violate conservation law for test
            allocated = budget // 2
            unallocated = 0
        else:
            allocated = budget
            unallocated = 0

        allocations = []
        if projects:
            share_per_proj = allocated // len(projects)
            remainder = allocated % len(projects)

            for idx, p in enumerate(projects):
                amt = share_per_proj + (remainder if idx == 0 else 0)
                allocations.append(
                    Allocation(
                        project_id=p.project_id,
                        allocated_amount_paise=amt,
                        marginal_impact_score=0.88,
                        base_score=0.90,
                        saturation_index=0.30,
                        reason_codes=[ReasonCode.HIGH_NEED, ReasonCode.LOW_SATURATION],
                        rank=idx + 1,
                        status=AllocationStatus.PROPOSED,
                    )
                )

        return OptimizationResult(
            run_id=run_id,
            status=OptimizationStatus.COMPLETED,
            budget_paise=budget,
            allocated_paise=allocated,
            unallocated_paise=unallocated,
            allocations=allocations,
            total_predicted_impact=185.4,
            average_saturation=0.30,
            underserved_region_allocation_share=0.75,
            weights=request.weights,
            constraints=request.constraints,
            calculation_versions={"solver": "fake-milp-v1"},
            created_at="2026-09-03T12:00:00Z",
        )


class FakeReallocationEngine:
    """Deterministic double for ReallocationEngine."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def reallocate(
        self,
        previous_run_id: str,
        previous_allocations: List[Allocation],
        performance_updates: Any,
        request: ReallocationRequest,
        realloc_run_id: str,
    ) -> ReallocationResult:
        if self.should_fail:
            raise RuntimeError("Fake reallocation engine deliberate failure")

        new_allocs = [a.model_copy(deep=True) for a in previous_allocations]
        changed_pids = [p.project_id for p in performance_updates] if performance_updates else []

        return ReallocationResult(
            run_id=realloc_run_id,
            previous_run_id=previous_run_id,
            old_allocations=previous_allocations,
            new_allocations=new_allocs,
            changed_projects=changed_pids,
            total_budget_shifted_paise=50000000,
            explanation=["Adjusted for Q2 delivery performance"],
            calculation_versions={"realloc": "fake-realloc-v1"},
            created_at="2026-09-03T12:00:00Z",
        )


class FakeDueDiligenceEngine:
    """Deterministic double for DueDiligenceEngine."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def evaluate(
        self,
        ngo_id: str,
        name: str,
        registration_number: Optional[str] = None,
        report_id: Optional[str] = None,
    ) -> DueDiligenceReport:
        if self.should_fail:
            raise RuntimeError("Fake due diligence engine deliberate failure")

        checks = [
            DueDiligenceCheck(
                check_name="fcra_registration",
                status=VerificationStatus.VERIFIED,
                source="MHA Portal",
                confidence=0.98,
                checked_at="2026-09-03T12:00:00Z",
            ),
            DueDiligenceCheck(
                check_name="12a_80g_validity",
                status=VerificationStatus.VERIFIED,
                source="Income Tax Portal",
                confidence=0.95,
                checked_at="2026-09-03T12:00:00Z",
            ),
        ]

        return DueDiligenceReport(
            report_id=report_id or "DD-ENGINE-STUB",
            ngo_id=ngo_id,
            overall_status=VerificationStatus.VERIFIED,
            risk_level=DueDiligenceRisk.LOW,
            checks=checks,
            flags=[],
            missing_documents=[],
            model_name="fake-due-diligence-v1",
            model_version="v1.0",
        )
