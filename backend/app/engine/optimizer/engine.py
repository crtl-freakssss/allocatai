from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from app.schemas.project import Project
from app.schemas.impact_dna import ImpactDNA
from app.schemas.saturation import SaturationResult
from app.schemas.optimization import OptimizationRequest, OptimizationResult
from app.schemas.allocation import Allocation
from app.schemas.enums import OptimizationStatus, AllocationStatus, ReasonCode
from app.engine.scoring.scorer import ScoringEngine
from app.engine.saturation.engine import RealSaturationEngine
from app.engine.marginal_impact.calculator import MarginalImpactCalculator
from app.engine.impact_dna.engine import RealImpactDNAEngine
from app.engine.optimizer.formulation import MILPOptimizerFormulation


class RealOptimizationEngine:
    """Production MILP portfolio optimizer implementing the OptimizationEngine Protocol."""

    def __init__(
        self,
        scoring_engine: Optional[ScoringEngine] = None,
        saturation_engine: Optional[RealSaturationEngine] = None,
        dna_engine: Optional[RealImpactDNAEngine] = None,
    ) -> None:
        self.scoring_engine = scoring_engine or ScoringEngine()
        self.saturation_engine = saturation_engine or RealSaturationEngine()
        self.dna_engine = dna_engine or RealImpactDNAEngine()

    def optimize(
        self,
        projects: List[Project],
        impact_dna_map: Dict[str, ImpactDNA],
        saturation_map: Dict[str, SaturationResult],
        request: OptimizationRequest,
        run_id: str,
    ) -> OptimizationResult:
        """Execute linear programming optimization, enforce conservation, and return full result."""
        budget = request.budget_paise
        n = len(projects)

        if n == 0:
            return OptimizationResult(
                run_id=run_id,
                status=OptimizationStatus.COMPLETED,
                budget_paise=budget,
                allocated_paise=0,
                unallocated_paise=budget,
                allocations=[],
                total_predicted_impact=0.0,
                average_saturation=0.0,
                underserved_region_allocation_share=0.0,
                weights=request.weights,
                constraints=request.constraints,
                calculation_versions={"solver": MILPOptimizerFormulation.SOLVER_VERSION},
                created_at=datetime.now(timezone.utc).isoformat(),
            )

        # 1. Enrich any missing DNA or Saturation
        project_ids = []
        requested_amounts = []
        project_scores = []
        project_states = []
        underserved_mask = []
        base_scores = []
        marginal_scores = []
        saturation_indices = []

        for p in projects:
            pid = p.project_id
            project_ids.append(pid)
            req_amt = p.financials.requested_amount_paise
            requested_amounts.append(req_amt)

            primary_state = p.geographies[0].state if p.geographies else "Maharashtra"
            project_states.append(primary_state)

            # Impact DNA
            dna = impact_dna_map.get(pid)
            if not dna:
                dna = self.dna_engine.generate(
                    project_id=pid,
                    name=p.name,
                    sector=p.sector.value,
                    requested_amount_paise=req_amt,
                    geographies=[g.model_dump() for g in p.geographies],
                    beneficiary_profile=p.beneficiary_profile.model_dump() if p.beneficiary_profile else None,
                )

            # Saturation
            sat = saturation_map.get(pid)
            if not sat:
                sat = self.saturation_engine.calculate(
                    project_id=pid,
                    state=primary_state,
                    sector=p.sector.value,
                    need_score=float(dna.need_score),
                )

            sat_idx = float(sat.saturation_index)
            saturation_indices.append(sat_idx)
            is_underserved = sat_idx < 0.40 or float(dna.need_score) > 0.85
            underserved_mask.append(is_underserved)

            # Marginal Impact
            marginal_res = MarginalImpactCalculator.calculate(
                project_id=pid,
                requested_amount_paise=req_amt,
                baseline_allocated_paise=0,
                expected_impact_score=float(dna.expected_impact_score),
                saturation_index=sat_idx,
                increment_paise=request.marginal_increment_paise,
            )
            marginal_scores.append(marginal_res.marginal_impact_score)

            # Multi-attribute utility score
            score = self.scoring_engine.calculate_score(
                impact_dna=dna,
                weights=request.weights,
                saturation_index=sat_idx,
                marginal_impact_score=marginal_res.marginal_impact_score,
            )
            base_scores.append(score)
            project_scores.append(score)

        # 2. Solve MILP Marginal-Impact Formulation
        decay_lambdas = [0.5 + 0.5 * s for s in saturation_indices]
        allocations_paise, total_allocated, unallocated, is_optimal = (
            MILPOptimizerFormulation.solve(
                budget_paise=budget,
                project_ids=project_ids,
                requested_amounts=requested_amounts,
                project_scores=project_scores,
                project_states=project_states,
                underserved_mask=underserved_mask,
                constraints=request.constraints,
                decay_lambdas=decay_lambdas,
            )
        )

        # 3. Build detailed allocations and rank
        # Sort by allocated amount descending, then by score descending
        alloc_items = []
        for i in range(n):
            alloc_amt = allocations_paise[i]
            pid = project_ids[i]
            req_amt = requested_amounts[i]
            sat_idx = saturation_indices[i]
            m_score = marginal_scores[i]
            b_score = base_scores[i]

            # Determine explainable reason codes from valid enum members
            codes = []
            if b_score >= 0.70:
                codes.append(ReasonCode.HIGH_NEED)
            if m_score >= 0.70:
                codes.append(ReasonCode.HIGH_MARGINAL_IMPACT)
            if sat_idx <= 0.35:
                codes.append(ReasonCode.LOW_SATURATION)
            if request.constraints.regional_equity_enabled and underserved_mask[i]:
                codes.append(ReasonCode.LOW_SATURATION)
            if alloc_amt > 0 and unallocated == 0:
                codes.append(ReasonCode.BUDGET_CONSTRAINT)

            # Ensure unique codes
            unique_codes = list(dict.fromkeys(codes))
            if not unique_codes:
                unique_codes.append(ReasonCode.HIGH_NEED)

            alloc_items.append(
                {
                    "project_id": pid,
                    "allocated_amount_paise": alloc_amt,
                    "marginal_impact_score": m_score,
                    "base_score": b_score,
                    "saturation_index": sat_idx,
                    "reason_codes": unique_codes,
                    "is_underserved": underserved_mask[i],
                }
            )

        # Assign ranks
        alloc_items.sort(key=lambda x: (x["allocated_amount_paise"], x["base_score"]), reverse=True)
        allocations: List[Allocation] = []
        for rank, item in enumerate(alloc_items, start=1):
            allocations.append(
                Allocation(
                    project_id=item["project_id"],
                    allocated_amount_paise=item["allocated_amount_paise"],
                    marginal_impact_score=item["marginal_impact_score"],
                    base_score=item["base_score"],
                    saturation_index=item["saturation_index"],
                    reason_codes=item["reason_codes"],
                    rank=rank,
                    status=AllocationStatus.PROPOSED,
                )
            )

        # 4. Compute portfolio analytics
        total_pred_impact = sum(
            (item["allocated_amount_paise"] / 10_000_000) * item["base_score"] * 5.0
            for item in alloc_items
        )

        if total_allocated > 0:
            avg_saturation = sum(
                item["saturation_index"] * (item["allocated_amount_paise"] / total_allocated)
                for item in alloc_items
            )
            underserved_share = sum(
                item["allocated_amount_paise"]
                for item in alloc_items
                if item["is_underserved"]
            ) / total_allocated
        else:
            avg_saturation = 0.0
            underserved_share = 0.0

        calculation_versions = {
            "solver": MILPOptimizerFormulation.SOLVER_VERSION,
            "scoring": ScoringEngine.VERSION,
            "saturation": RealSaturationEngine.VERSION,
            "marginal": MarginalImpactCalculator.VERSION,
        }

        return OptimizationResult(
            run_id=run_id,
            status=OptimizationStatus.COMPLETED,
            budget_paise=budget,
            allocated_paise=total_allocated,
            unallocated_paise=unallocated,
            allocations=allocations,
            total_predicted_impact=round(total_pred_impact, 4),
            average_saturation=round(avg_saturation, 4),
            underserved_region_allocation_share=round(underserved_share, 4),
            weights=request.weights,
            constraints=request.constraints,
            calculation_versions=calculation_versions,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
