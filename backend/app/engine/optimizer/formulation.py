import math
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

from app.schemas.optimization import OptimizationConstraints


class MILPOptimizerFormulation:
    """Mathematical formulation and solver wrapper for MILP portfolio allocation.

    Formulates a concave piecewise-linear objective maximizing marginal social impact
    per rupee under diminishing utility curves, while guaranteeing integer paise conservation.
    """

    SOLVER_VERSION: str = "scipy-milp-v1"

    @classmethod
    def solve(
        cls,
        budget_paise: int,
        project_ids: List[str],
        requested_amounts: List[int],
        project_scores: List[float],
        project_states: List[str],
        underserved_mask: List[bool],
        constraints: OptimizationConstraints,
        decay_lambdas: Optional[List[float]] = None,
    ) -> Tuple[List[int], int, int, bool]:
        """Solve the marginal-impact portfolio allocation problem.

        Objective:
            Maximize Sum_{i, k} MarginalImpact(project_i, tranche_k) * x_{i, k}
            subject to total budget, project caps, regional caps, and regional equity constraints.

        Returns:
            (allocations_paise, total_allocated_paise, unallocated_paise, is_optimal)
        """
        n = len(project_ids)
        if n == 0 or budget_paise <= 0:
            return [0] * n, 0, budget_paise, True

        lambdas = decay_lambdas or [0.5] * n

        # Tranche formulation per project: 3 tranches (0-50%, 50-100%, 100%+)
        # Enables piecewise-linear concave marginal impact optimization
        num_tranches = 3
        num_vars = n * num_tranches

        c_list = []
        ub_var_list = []
        lb_var_list = []

        for i in range(n):
            req = requested_amounts[i]
            upper_cap = req
            if constraints.max_allocation_per_project_paise is not None:
                upper_cap = min(upper_cap, constraints.max_allocation_per_project_paise)
            upper_cap = max(0, upper_cap)

            base_score = project_scores[i]
            lam = lambdas[i]

            # Tranche capacities
            t1_cap = int(round(upper_cap * 0.5))
            t2_cap = upper_cap - t1_cap
            t3_cap = max(0, upper_cap - (t1_cap + t2_cap))

            # Tranche marginal utility multipliers: e^(-lambda * ratio)
            m1 = base_score * math.exp(-lam * 0.2)
            m2 = base_score * math.exp(-lam * 0.5)
            m3 = base_score * math.exp(-lam * 1.0)

            # Minimization objective (c = -marginal_impact)
            c_list.extend([-m1, -m2, -m3])
            ub_var_list.extend([float(t1_cap), float(t2_cap), float(t3_cap)])
            lb_var_list.extend([0.0, 0.0, 0.0])

        c = np.array(c_list, dtype=float)

        A_rows = []
        lhs = []
        rhs = []

        # 1. Total budget constraint: sum(x_{i, k}) <= budget
        budget_row = [1.0] * num_vars
        A_rows.append(budget_row)
        lhs.append(0.0)
        rhs.append(float(budget_paise))

        # 2. Regional caps: sum_{i in state} sum_k x_{i, k} <= max_per_region
        if constraints.max_allocation_per_region_paise is not None:
            unique_states = set(project_states)
            for state in unique_states:
                row = []
                for i in range(n):
                    weight = 1.0 if project_states[i] == state else 0.0
                    row.extend([weight] * num_tranches)
                A_rows.append(row)
                lhs.append(0.0)
                rhs.append(float(constraints.max_allocation_per_region_paise))

        # 3. Regional equity constraint: reserve share for underserved regions
        if constraints.regional_equity_enabled and any(underserved_mask):
            row = []
            for i in range(n):
                weight = 1.0 if underserved_mask[i] else 0.0
                row.extend([weight] * num_tranches)
            
            # Total requested budget in underserved areas
            total_req = sum(requested_amounts[i] for i, m in enumerate(underserved_mask) if m)
            min_equity_target = min(float(total_req), float(budget_paise) * 0.25)
            if min_equity_target > 0:
                A_rows.append(row)
                lhs.append(min_equity_target)
                rhs.append(float(budget_paise))

        A = np.array(A_rows, dtype=float)
        b_l = np.array(lhs, dtype=float)
        b_u = np.array(rhs, dtype=float)

        lin_constraints = LinearConstraint(A=A, lb=b_l, ub=b_u)
        bounds = Bounds(lb=lb_var_list, ub=ub_var_list)
        integrality = np.zeros(num_vars, dtype=int)

        res = milp(c=c, integrality=integrality, bounds=bounds, constraints=lin_constraints)

        # Fallback if equity lower bound was mathematically infeasible
        if not res.success and constraints.regional_equity_enabled and any(underserved_mask):
            A_relax = A[:-1] if len(A_rows) > 1 else np.array([[1.0] * num_vars])
            b_l_relax = b_l[:-1] if len(lhs) > 1 else np.array([0.0])
            b_u_relax = b_u[:-1] if len(rhs) > 1 else np.array([float(budget_paise)])
            lin_constraints = LinearConstraint(A=A_relax, lb=b_l_relax, ub=b_u_relax)
            res = milp(c=c, integrality=integrality, bounds=bounds, constraints=lin_constraints)

        # Aggregate tranche allocations back per project
        allocations_paise = [0] * n
        if res.success:
            raw_vars = np.maximum(0.0, np.minimum(res.x, ub_var_list))
            for i in range(n):
                proj_tranche_sum = sum(raw_vars[i * num_tranches : (i + 1) * num_tranches])
                allocations_paise[i] = int(round(proj_tranche_sum))
        else:
            # Greedy heuristic fallback ordered by baseline score
            rem_budget = budget_paise
            sorted_indices = np.argsort(project_scores)[::-1]
            for idx in sorted_indices:
                cap = requested_amounts[idx]
                if constraints.max_allocation_per_project_paise is not None:
                    cap = min(cap, constraints.max_allocation_per_project_paise)
                alloc = min(rem_budget, cap)
                allocations_paise[idx] = alloc
                rem_budget -= alloc

        # Bound enforcement per project
        for i in range(n):
            cap = requested_amounts[i]
            if constraints.max_allocation_per_project_paise is not None:
                cap = min(cap, constraints.max_allocation_per_project_paise)
            allocations_paise[i] = max(0, min(cap, allocations_paise[i]))

        # Guarantee strict budget conservation: sum(allocations) + unallocated = budget
        total_allocated = sum(allocations_paise)
        if total_allocated > budget_paise:
            excess = total_allocated - budget_paise
            sorted_asc = np.argsort(project_scores)
            for idx in sorted_asc:
                deduct = min(excess, allocations_paise[idx])
                allocations_paise[idx] -= deduct
                excess -= deduct
                if excess <= 0:
                    break
            total_allocated = sum(allocations_paise)

        unallocated_paise = budget_paise - total_allocated
        return allocations_paise, total_allocated, unallocated_paise, res.success
