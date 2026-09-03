import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.reallocation_run import ReallocationRun
from app.repositories.base import BaseRepository


class ReallocationRepository(BaseRepository[ReallocationRun]):
    """Data access repository for mid-cycle ReallocationRun executions."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, ReallocationRun)

    def create(
        self,
        public_id: str,
        previous_optimization_id: uuid.UUID,
        budget_paise: int,
        performance_snapshot: Dict[str, Any],
        calculation_versions: Dict[str, Any],
        result_snapshot: Optional[Dict[str, Any]] = None,
    ) -> ReallocationRun:
        """Create and persist a new reallocation run referencing a prior optimization run."""
        realloc = ReallocationRun(
            public_id=public_id,
            previous_optimization_id=previous_optimization_id,
            budget_paise=budget_paise,
            performance_snapshot=performance_snapshot,
            calculation_versions=calculation_versions,
            result_snapshot=result_snapshot,
        )
        return self.add(realloc, flush=True)

    def get_by_public_id(self, public_id: str) -> Optional[ReallocationRun]:
        """Fetch reallocation run by public ID (e.g. REA-0001)."""
        stmt = select(ReallocationRun).where(ReallocationRun.public_id == public_id)
        return self.session.scalar(stmt)

    def get_by_previous_optimization_id(self, prev_run_id: uuid.UUID) -> List[ReallocationRun]:
        """Fetch all reallocation runs stemming from a base optimization run."""
        stmt = (
            select(ReallocationRun)
            .where(ReallocationRun.previous_optimization_id == prev_run_id)
            .order_by(ReallocationRun.created_at.desc(), ReallocationRun.id.asc())
        )
        return list(self.session.scalars(stmt).all())

    def list(self, page: int = 1, page_size: int = 20) -> Tuple[List[ReallocationRun], int]:
        """List reallocation runs with deterministic pagination."""
        offset = max(0, (page - 1) * page_size)
        total_stmt = select(func.count()).select_from(ReallocationRun)
        total = self.session.scalar(total_stmt) or 0

        stmt = (
            select(ReallocationRun)
            .order_by(ReallocationRun.created_at.desc(), ReallocationRun.id.asc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(self.session.scalars(stmt).all())
        return items, total

    def save_result_snapshot(
        self,
        run: ReallocationRun,
        result_snapshot: Dict[str, Any],
    ) -> ReallocationRun:
        """Save results of reallocation execution."""
        run.result_snapshot = result_snapshot
        self.session.flush()
        return run
