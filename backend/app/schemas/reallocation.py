from pydantic import BaseModel, Field
from app.schemas.allocation import Allocation
from app.schemas.optimization import OptimizationConstraints, OptimizationWeights


class ProjectPerformanceUpdate(BaseModel):
    """Mid-cycle progress and KPI updates reported for an active project."""

    project_id: str = Field(..., description="Referenced project public ID, e.g. PRJ-0001")

    actual_beneficiaries: int | None = Field(default=None, ge=0, description="Verified reached beneficiaries to date")
    actual_spend_paise: int | None = Field(default=None, ge=0, strict=True, description="Cumulative actual expenditure in paise")
    progress_percent: float | None = Field(default=None, ge=0, le=100, description="Milestone completion percentage [0, 100]")
    updated_risk_score: float | None = Field(default=None, ge=0, le=1, description="Revised operational risk score [0, 1]")
    updated_impact_score: float | None = Field(default=None, ge=0, le=1, description="Revised expected impact score [0, 1]")


class ReallocationRequest(BaseModel):
    """Payload to trigger a mid-cycle capital reallocation run."""

    previous_run_id: str = Field(..., description="Public identifier of base optimization run, e.g. OPT-0001")
    budget_paise: int = Field(..., gt=0, strict=True, description="Total active budget available for reallocation in paise")
    performance_updates: list[ProjectPerformanceUpdate] = Field(..., description="Empirical performance updates")
    weights: OptimizationWeights = Field(..., description="Updated objective weights")
    constraints: OptimizationConstraints = Field(..., description="Updated policy constraints")


class ReallocationResult(BaseModel):
    """Output results of a completed reallocation run."""

    run_id: str = Field(..., description="Public identifier, e.g. REA-0001")
    previous_run_id: str = Field(..., description="Referenced prior optimization run ID, e.g. OPT-0001")

    old_allocations: list[Allocation] = Field(..., description="Prior allocations before performance adjustment")
    new_allocations: list[Allocation] = Field(..., description="Revised allocations post-reallocation")

    changed_projects: list[str] = Field(..., description="List of project IDs with adjusted funding levels")
    total_budget_shifted_paise: int = Field(..., ge=0, strict=True, description="Total quantum of capital moved in paise")

    explanation: list[str] = Field(..., description="Human-interpretable rationales for funding adjustments")

    calculation_versions: dict[str, str] = Field(..., description="Version tags of reallocation engines used")
    created_at: str = Field(..., description="UTC ISO timestamp of reallocation execution")
