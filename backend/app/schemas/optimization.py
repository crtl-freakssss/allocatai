import math
from pydantic import BaseModel, Field, model_validator
from app.schemas.enums import OptimizationStatus
from app.schemas.allocation import Allocation


class OptimizationWeights(BaseModel):
    """User-configurable multidimensional objective weights for portfolio optimization."""

    need: float = Field(..., ge=0, le=1, description="Weight for socioeconomic need [0, 1]")
    marginal_impact: float = Field(..., ge=0, le=1, description="Weight for marginal utility [0, 1]")
    cost_efficiency: float = Field(..., ge=0, le=1, description="Weight for cost efficiency [0, 1]")
    evidence: float = Field(..., ge=0, le=1, description="Weight for evidence strength [0, 1]")
    scalability: float = Field(..., ge=0, le=1, description="Weight for project scalability [0, 1]")
    equity: float = Field(..., ge=0, le=1, description="Weight for regional equity [0, 1]")
    risk_penalty: float = Field(..., ge=0, le=1, description="Penalty discount for execution risk [0, 1]")

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "OptimizationWeights":
        total = (
            self.need
            + self.marginal_impact
            + self.cost_efficiency
            + self.evidence
            + self.scalability
            + self.equity
            + self.risk_penalty
        )
        if not math.isclose(total, 1.0, abs_tol=1e-3):
            raise ValueError(f"Optimization weights must sum to 1.0, got {total:.4f}")
        return self


class OptimizationConstraints(BaseModel):
    """Policy and budget limits governing the MILP optimization solver."""

    max_allocation_per_project_paise: int | None = Field(
        default=None,
        ge=0,
        strict=True,
        description="Upper cap on funding for any single project in paise",
    )
    max_allocation_per_region_paise: int | None = Field(
        default=None,
        ge=0,
        strict=True,
        description="Upper cap on funding for any single state/region in paise",
    )
    minimum_allocation_per_project_paise: int | None = Field(
        default=None,
        ge=0,
        strict=True,
        description="Minimum feasible allocation tranche in paise if project is selected",
    )
    require_full_budget_allocation: bool = Field(
        default=True,
        description="Enforce that the entire available budget is allocated if mathematically feasible",
    )
    regional_equity_enabled: bool = Field(
        default=True,
        description="Enforce geographic distribution constraints across under-represented states",
    )


class OptimizationRequest(BaseModel):
    """Payload to initiate a portfolio optimization run."""

    budget_paise: int = Field(..., gt=0, strict=True, description="Total capital available for allocation in paise")
    project_ids: list[str] = Field(..., min_length=1, description="Candidate project public IDs for optimization")
    weights: OptimizationWeights = Field(..., description="Weighting coefficients for objective function")
    constraints: OptimizationConstraints = Field(..., description="Policy constraints for the solver")
    marginal_increment_paise: int = Field(
        default=10_000_000,
        gt=0,
        strict=True,
        description="Evaluation increment in paise (default ₹1 Lakh = 10,000,000 paise)",
    )


class OptimizationResult(BaseModel):
    """Output results of a completed portfolio optimization run."""

    run_id: str = Field(..., description="Public identifier, e.g. OPT-0001")
    status: OptimizationStatus = Field(..., description="Run execution status")

    budget_paise: int = Field(..., gt=0, strict=True, description="Total target budget in paise")
    allocated_paise: int = Field(..., ge=0, strict=True, description="Sum of recommended allocations in paise")
    unallocated_paise: int = Field(..., ge=0, strict=True, description="Unspent budget residue in paise")

    allocations: list[Allocation] = Field(..., description="Project-level allocation recommendations")

    total_predicted_impact: float = Field(..., ge=0, description="Projected aggregate impact metric score")
    average_saturation: float = Field(..., ge=0, le=1, description="Portfolio-weighted average saturation index")
    underserved_region_allocation_share: float = Field(
        ...,
        ge=0,
        le=1,
        description="Fraction of total funding awarded to high-need, low-saturation regions",
    )

    weights: OptimizationWeights = Field(..., description="Objective weights applied")
    constraints: OptimizationConstraints = Field(..., description="Constraints applied")

    calculation_versions: dict[str, str] = Field(..., description="Engine and solver versions for reproducibility")
    created_at: str = Field(..., description="UTC ISO timestamp of run execution")

    @model_validator(mode="after")
    def validate_budget_invariant(self) -> "OptimizationResult":
        """Enforce the contract budget conservation invariant: allocated + unallocated == budget."""
        if self.allocated_paise + self.unallocated_paise != self.budget_paise:
            raise ValueError(
                f"Budget invariant violated: allocated ({self.allocated_paise}) + "
                f"unallocated ({self.unallocated_paise}) != budget ({self.budget_paise})"
            )
        return self
