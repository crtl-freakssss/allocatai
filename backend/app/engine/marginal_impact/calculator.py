import math
from app.schemas.marginal_impact import MarginalImpactResult, DEFAULT_INCREMENT_PAISE


class MarginalImpactCalculator:
    """Deterministic marginal impact calculator modeling diminishing utility curves."""

    VERSION: str = "marginal-v1"

    @classmethod
    def calculate(
        cls,
        project_id: str,
        requested_amount_paise: int,
        baseline_allocated_paise: int = 0,
        expected_impact_score: float = 0.8,
        saturation_index: float = 0.5,
        increment_paise: int = DEFAULT_INCREMENT_PAISE,
    ) -> MarginalImpactResult:
        """Compute the incremental marginal impact deliverable by the next funding increment.

        Diminishing returns model:
        As allocation approaches or exceeds requested amount, each additional rupee yields
        progressively lower incremental social utility. Regional saturation accelerates this decay.
        """
        req_paise = max(1, requested_amount_paise)
        funding_ratio = baseline_allocated_paise / req_paise

        # Decay parameter lambda scaled by regional saturation [0.5, 1.0]
        decay_lambda = 0.5 + (0.5 * saturation_index)
        diminishing_factor = max(0.01, min(1.0, math.exp(-decay_lambda * funding_ratio)))

        # Baseline impact at current funding level
        total_lakhs = max(1.0, req_paise / DEFAULT_INCREMENT_PAISE)
        nominal_impact_per_lakh = (expected_impact_score * 100.0) / total_lakhs

        baseline_lakhs = baseline_allocated_paise / DEFAULT_INCREMENT_PAISE
        baseline_impact = round(nominal_impact_per_lakh * baseline_lakhs * (1.0 - 0.2 * funding_ratio), 4)
        baseline_impact = max(0.0, baseline_impact)

        # Marginal impact per lakh with diminishing returns factor applied
        effective_impact_per_lakh = round(nominal_impact_per_lakh * diminishing_factor, 4)

        increment_lakhs = increment_paise / DEFAULT_INCREMENT_PAISE
        incremental_impact = round(effective_impact_per_lakh * increment_lakhs, 4)
        projected_impact = round(baseline_impact + incremental_impact, 4)

        # Normalized marginal score in [0.0, 1.0]
        marginal_score = max(0.01, min(1.0, round(expected_impact_score * diminishing_factor, 5)))

        return MarginalImpactResult(
            project_id=project_id,
            increment_paise=increment_paise,
            baseline_budget_paise=baseline_allocated_paise,
            projected_budget_paise=baseline_allocated_paise + increment_paise,
            baseline_impact=baseline_impact,
            projected_impact=projected_impact,
            incremental_impact=incremental_impact,
            impact_per_lakh=effective_impact_per_lakh,
            marginal_impact_score=marginal_score,
            diminishing_return_factor=round(diminishing_factor, 5),
            calculation_version=cls.VERSION,
        )
