from typing import Protocol, List, Dict, Optional, Any
from app.schemas import (
    ExtractionResult,
    ImpactDNA,
    SaturationResult,
    OptimizationRequest,
    OptimizationResult,
    ReallocationRequest,
    ReallocationResult,
    DueDiligenceReport,
    Project,
    Allocation,
    ProjectPerformanceUpdate,
)


class ExtractionEngine(Protocol):
    """Protocol for AI extraction of project specifications from proposal documents."""

    def extract(
        self,
        proposal_id: str,
        document_id: str,
        filename: str,
        mime_type: str,
        storage_key: str,
    ) -> ExtractionResult:
        ...


class ImpactDNAEngine(Protocol):
    """Protocol for multidimensional Impact DNA dimension generation."""

    def generate(
        self,
        project_id: str,
        name: str,
        sector: str,
        requested_amount_paise: int,
        geographies: List[Dict[str, Any]],
        beneficiary_profile: Optional[Dict[str, Any]] = None,
    ) -> ImpactDNA:
        ...


class SaturationEngine(Protocol):
    """Protocol for regional saturation and demographic capacity assessment."""

    def calculate(
        self,
        project_id: str,
        state: str,
        sector: str,
        need_score: float,
    ) -> SaturationResult:
        ...


class OptimizationEngine(Protocol):
    """Protocol for the MILP portfolio optimization engine."""

    def optimize(
        self,
        projects: List[Project],
        impact_dna_map: Dict[str, ImpactDNA],
        saturation_map: Dict[str, SaturationResult],
        request: OptimizationRequest,
        run_id: str,
    ) -> OptimizationResult:
        ...


class ReallocationEngine(Protocol):
    """Protocol for performance-adjusted mid-cycle capital reallocation."""

    def reallocate(
        self,
        previous_run_id: str,
        previous_allocations: List[Allocation],
        performance_updates: List[ProjectPerformanceUpdate],
        request: ReallocationRequest,
        realloc_run_id: str,
    ) -> ReallocationResult:
        ...


class DueDiligenceEngine(Protocol):
    """Protocol for automated NGO regulatory and operational risk auditing."""

    def evaluate(
        self,
        ngo_id: str,
        name: str,
        registration_number: Optional[str] = None,
        report_id: Optional[str] = None,
    ) -> DueDiligenceReport:
        ...
