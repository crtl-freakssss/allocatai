import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any, Union
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.optimization_run import OptimizationRun
from app.repositories.base import BaseRepository


class OptimizationRepository(BaseRepository[OptimizationRun]):
    """Data access repository for OptimizationRun executions.

    Enforces contract immutability once a run transitions to COMPLETED.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(session, OptimizationRun)

    def create(
        self,
        public_id: str,
        budget_paise: int,
        weights: Dict[str, Any],
        constraints: Dict[str, Any],
        calculation_versions: Dict[str, Any],
        input_snapshot: Dict[str, Any],
        status: str = "QUEUED",
    ) -> OptimizationRun:
        """Create and persist a new portfolio optimization run."""
        run = OptimizationRun(
            public_id=public_id,
            budget_paise=budget_paise,
            status=status,
            weights=weights,
            constraints=constraints,
            calculation_versions=calculation_versions,
            input_snapshot=input_snapshot,
        )
        return self.add(run, flush=True)

    def get_by_public_id(self, public_id: str) -> Optional[OptimizationRun]:
        """Fetch optimization run by public ID (e.g. OPT-0001)."""
        stmt = select(OptimizationRun).where(OptimizationRun.public_id == public_id)
        return self.session.scalar(stmt)

    def get_completed_run(self, identifier: Union[str, uuid.UUID]) -> Optional[OptimizationRun]:
        """Fetch a completed optimization run by UUID or public ID."""
        if isinstance(identifier, uuid.UUID):
            stmt = select(OptimizationRun).where(
                OptimizationRun.id == identifier,
                OptimizationRun.status == "COMPLETED",
            )
        else:
            stmt = select(OptimizationRun).where(
                OptimizationRun.public_id == identifier,
                OptimizationRun.status == "COMPLETED",
            )
        return self.session.scalar(stmt)

    def list(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[OptimizationRun], int]:
        """List optimization runs with deterministic pagination."""
        offset = max(0, (page - 1) * page_size)

        filters = []
        if status is not None:
            filters.append(OptimizationRun.status == status)

        total_stmt = select(func.count()).select_from(OptimizationRun)
        if filters:
            total_stmt = total_stmt.where(*filters)
        total = self.session.scalar(total_stmt) or 0

        stmt = select(OptimizationRun)
        if filters:
            stmt = stmt.where(*filters)

        stmt = stmt.order_by(OptimizationRun.created_at.desc(), OptimizationRun.id.asc()).offset(offset).limit(page_size)
        items = list(self.session.scalars(stmt).all())
        return items, total

    def update_status(self, run: OptimizationRun, status: str) -> OptimizationRun:
        """Update solver execution status."""
        if run.status == "COMPLETED" and status != "COMPLETED":
            raise ValueError(f"Cannot transition run '{run.public_id}' out of immutable COMPLETED state")
        run.status = status
        if status == "COMPLETED" and run.completed_at is None:
            run.completed_at = datetime.now(timezone.utc)
        self.session.flush()
        return run

    def save_result_snapshot(
        self,
        run: OptimizationRun,
        result_snapshot: Dict[str, Any],
        total_predicted_impact: Optional[Decimal] = None,
        mark_completed: bool = True,
    ) -> OptimizationRun:
        """Save solver result snapshot and seal run as COMPLETED."""
        if run.status == "COMPLETED":
            raise ValueError(f"Run '{run.public_id}' is already COMPLETED and immutable; result snapshot cannot be altered")

        run.result_snapshot = result_snapshot
        if total_predicted_impact is not None:
            run.total_predicted_impact = total_predicted_impact
        if mark_completed:
            run.status = "COMPLETED"
            run.completed_at = datetime.now(timezone.utc)
        self.session.flush()
        return run

    def mutate_input_snapshot(self, run: OptimizationRun, new_input_snapshot: Dict[str, Any]) -> OptimizationRun:
        """Guarded mutation of input snapshot (forbidden if already COMPLETED)."""
        if run.status == "COMPLETED":
            raise ValueError(f"Run '{run.public_id}' is COMPLETED; input snapshot is immutable")
        run.input_snapshot = new_input_snapshot
        self.session.flush()
        return run
