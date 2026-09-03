from typing import Dict, Any, Optional
from app.schemas.optimization import OptimizationWeights
from app.schemas.impact_dna import ImpactDNA


class ScoringEngine:
    """Deterministic multidimensional scoring engine for CSR projects."""

    VERSION: str = "scoring-v1"

    @classmethod
    def calculate_score(
        cls,
        impact_dna: ImpactDNA,
        weights: OptimizationWeights,
        saturation_index: float = 0.5,
        marginal_impact_score: Optional[float] = None,
    ) -> float:
        """Compute a deterministic multi-attribute utility score normalized to [0.0, 1.0].

        Higher score implies stronger investment priority:
        - High socioeconomic need increases score
        - High expected impact / marginal impact increases score
        - High cost efficiency increases score
        - High evidence strength increases score
        - High scalability increases score
        - Low saturation (high equity need: 1 - saturation_index) increases score
        - High implementation risk penalizes score
        """
        # Marginal utility defaults to expected impact if not separately computed
        marginal_val = (
            marginal_impact_score
            if marginal_impact_score is not None
            else float(impact_dna.expected_impact_score)
        )

        # Equity score is higher in underserved/low-saturation regions
        equity_val = max(0.0, min(1.0, 1.0 - saturation_index))

        score = (
            weights.need * float(impact_dna.need_score)
            + weights.marginal_impact * marginal_val
            + weights.cost_efficiency * float(impact_dna.cost_efficiency_score)
            + weights.evidence * float(impact_dna.evidence_strength_score)
            + weights.scalability * float(impact_dna.scalability_score)
            + weights.equity * equity_val
            - weights.risk_penalty * float(impact_dna.implementation_risk_score)
        )

        # Clamp strictly to [0.0, 1.0]
        return max(0.0, min(1.0, round(score, 5)))
