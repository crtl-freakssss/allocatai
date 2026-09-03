from pydantic import BaseModel, Field

DEFAULT_INCREMENT_PAISE: int = 10_000_000  # ₹1,00,000 in paise


class MarginalImpactResult(BaseModel):
    """Diminishing returns evaluation on incremental funding tranches."""

    project_id: str = Field(..., description="Referenced project public ID, e.g. PRJ-0001")

    increment_paise: int = Field(
        default=DEFAULT_INCREMENT_PAISE,
        gt=0,
        strict=True,
        description="Incremental evaluation funding step in paise (default ₹1 Lakh = 10,000,000 paise)",
    )

    baseline_budget_paise: int = Field(..., ge=0, strict=True, description="Starting budget tier in paise")
    projected_budget_paise: int = Field(..., gt=0, strict=True, description="Budget tier after increment in paise")

    baseline_impact: float = Field(..., ge=0, description="Total impact deliverable at baseline budget")
    projected_impact: float = Field(..., ge=0, description="Total impact deliverable at projected budget")

    incremental_impact: float = Field(..., ge=0, description="Net impact gain from incremental funding tranche")
    impact_per_lakh: float = Field(..., ge=0, description="Effective impact output per ₹1,00,000 allocated")

    marginal_impact_score: float = Field(..., ge=0, le=1, description="Normalized marginal utility score [0, 1]")

    diminishing_return_factor: float = Field(
        ...,
        ge=0,
        le=1,
        description="Decay multiplier [0, 1] reflecting saturation and diminishing returns",
    )

    calculation_version: str = Field(default="marginal-v1", description="Marginal impact engine calculation version")
