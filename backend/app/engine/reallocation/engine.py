from datetime import datetime, timezone
from typing import List, Dict, Any
from app.schemas.allocation import Allocation
from app.schemas.reallocation import (
    ReallocationRequest,
    ReallocationResult,
    ProjectPerformanceUpdate,
)
from app.schemas.enums import AllocationStatus, ReasonCode


class RealReallocationEngine:
    """Production mid-cycle capital reallocation engine based on empirical project delivery velocity."""

    VERSION: str = "realloc-v1"

    def reallocate(
        self,
        previous_run_id: str,
        previous_allocations: List[Allocation],
        performance_updates: List[ProjectPerformanceUpdate],
        request: ReallocationRequest,
        realloc_run_id: str,
    ) -> ReallocationResult:
        """Evaluate milestones delivery and shift capital from underperforming to high-velocity interventions."""
        perf_map = {p.project_id: p for p in performance_updates}

        new_allocations: List[Allocation] = []
        changed_projects: List[str] = []
        total_budget_shifted = 0
        explanations: List[str] = []

        # 1. Identify lagging projects with excess capital
        freed_capital_paise = 0
        working_allocations: Dict[str, int] = {}

        for alloc in previous_allocations:
            pid = alloc.project_id
            curr_amt = alloc.allocated_amount_paise
            perf = perf_map.get(pid)

            if perf and perf.progress_percent < 40.0:
                # Project is significantly behind schedule; reclaim 20% of unutilized capital
                trim = int(curr_amt * 0.20)
                working_allocations[pid] = curr_amt - trim
                freed_capital_paise += trim
                changed_projects.append(pid)
                explanations.append(
                    f"Trimmed ₹{trim // 100_000} Lakhs from {pid} due to milestone delay ({perf.progress_percent}% progress)."
                )
            else:
                working_allocations[pid] = curr_amt

        # 2. Redirect freed capital to top performing projects (>75% progress)
        high_performers = [
            alloc.project_id
            for alloc in previous_allocations
            if alloc.project_id in perf_map and perf_map[alloc.project_id].progress_percent >= 75.0
        ]

        if high_performers and freed_capital_paise > 0:
            share = freed_capital_paise // len(high_performers)
            remainder = freed_capital_paise % len(high_performers)
            for idx, pid in enumerate(high_performers):
                boost = share + (remainder if idx == 0 else 0)
                working_allocations[pid] += boost
                total_budget_shifted += boost
                if pid not in changed_projects:
                    changed_projects.append(pid)
                explanations.append(
                    f"Reallocated ₹{boost // 100_000} Lakhs to high-velocity project {pid}."
                )
        else:
            # If no high performers or no freed capital, nominal small shift
            total_budget_shifted = freed_capital_paise

        # 3. Build new allocations list preserving ranks
        for alloc in previous_allocations:
            pid = alloc.project_id
            new_amt = working_allocations.get(pid, alloc.allocated_amount_paise)
            reasons = list(alloc.reason_codes)

            if pid in high_performers:
                if ReasonCode.HIGH_MARGINAL_IMPACT not in reasons:
                    reasons.append(ReasonCode.HIGH_MARGINAL_IMPACT)

            new_allocations.append(
                Allocation(
                    project_id=pid,
                    allocated_amount_paise=new_amt,
                    marginal_impact_score=alloc.marginal_impact_score,
                    base_score=alloc.base_score,
                    saturation_index=alloc.saturation_index,
                    reason_codes=reasons,
                    rank=alloc.rank,
                    status=AllocationStatus.PROPOSED,
                )
            )

        # Ensure at least one explanation item
        if not explanations:
            explanations.append("All projects on schedule; existing allocation distribution validated.")

        return ReallocationResult(
            run_id=realloc_run_id,
            previous_run_id=previous_run_id,
            old_allocations=previous_allocations,
            new_allocations=new_allocations,
            changed_projects=changed_projects,
            total_budget_shifted_paise=total_budget_shifted,
            explanation=explanations,
            calculation_versions={"reallocation": self.VERSION},
            created_at=datetime.now(timezone.utc).isoformat(),
        )
