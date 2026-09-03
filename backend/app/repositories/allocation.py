import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.allocation import Allocation
from app.repositories.base import BaseRepository


class AllocationRepository(BaseRepository[Allocation]):
    """Data access repository for project funding allocations within optimization runs."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Allocation)

    def create(
        self,
        optimization_run_id: uuid.UUID,
        project_id: uuid.UUID,
        allocated_amount: int,
        marginal_score: Decimal,
        base_score: Decimal,
        saturation_index: Decimal,
        reason_codes: Dict[str, Any],
        rank: int,
        status: str = "PROPOSED",
    ) -> Allocation:
        """Create and persist a single project allocation."""
        alloc = Allocation(
            optimization_run_id=optimization_run_id,
            project_id=project_id,
            allocated_amount=allocated_amount,
            marginal_score=marginal_score,
            base_score=base_score,
            saturation_index=saturation_index,
            reason_codes=reason_codes,
            rank=rank,
            status=status,
        )
        return self.add(alloc, flush=True)

    def bulk_create(self, allocations: List[Allocation]) -> List[Allocation]:
        """Persist multiple allocations efficiently within current transaction."""
        for alloc in allocations:
            if not alloc.status:
                alloc.status = "PROPOSED"
            self.session.add(alloc)
        self.session.flush()
        return allocations

    def list_by_optimization_run(self, run_id: uuid.UUID) -> List[Allocation]:
        """Fetch all allocations belonging to an optimization run ordered by rank."""
        stmt = (
            select(Allocation)
            .where(Allocation.optimization_run_id == run_id)
            .order_by(Allocation.rank.asc(), Allocation.id.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_by_run_and_project(
        self,
        run_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Optional[Allocation]:
        """Fetch a specific project's allocation in an optimization run."""
        stmt = select(Allocation).where(
            Allocation.optimization_run_id == run_id,
            Allocation.project_id == project_id,
        )
        return self.session.scalar(stmt)

    def update_status(self, allocation: Allocation, status: str) -> Allocation:
        """Update review status of an allocation (e.g. APPROVED, REJECTED)."""
        allocation.status = status
        self.session.flush()
        return allocation
