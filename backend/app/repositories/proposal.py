import uuid
from typing import Optional, Tuple, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.proposal import Proposal
from app.repositories.base import BaseRepository


class ProposalRepository(BaseRepository[Proposal]):
    """Data access repository for Proposal entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Proposal)

    def create(
        self,
        public_id: str,
        ngo_id: uuid.UUID,
        title: str,
        status: str = "UPLOADED",
        source_type: str = "DIRECT_SUBMISSION",
    ) -> Proposal:
        """Create and persist a new proposal record."""
        proposal = Proposal(
            public_id=public_id,
            ngo_id=ngo_id,
            title=title,
            status=status,
            source_type=source_type,
        )
        return self.add(proposal, flush=True)

    def get_by_public_id(self, public_id: str) -> Optional[Proposal]:
        """Fetch proposal by authoritative public identifier (e.g. PRO-0001)."""
        stmt = select(Proposal).where(Proposal.public_id == public_id)
        return self.session.scalar(stmt)

    def exists_by_public_id(self, public_id: str) -> bool:
        """Check whether a proposal with the given public ID exists."""
        stmt = select(func.count()).select_from(Proposal).where(Proposal.public_id == public_id)
        count = self.session.scalar(stmt) or 0
        return count > 0

    def list(
        self,
        ngo_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Proposal], int]:
        """List proposals with deterministic pagination and optional filters."""
        offset = max(0, (page - 1) * page_size)

        filters = []
        if ngo_id is not None:
            filters.append(Proposal.ngo_id == ngo_id)
        if status is not None:
            filters.append(Proposal.status == status)

        total_stmt = select(func.count()).select_from(Proposal)
        if filters:
            total_stmt = total_stmt.where(*filters)
        total = self.session.scalar(total_stmt) or 0

        stmt = select(Proposal)
        if filters:
            stmt = stmt.where(*filters)

        stmt = stmt.order_by(Proposal.created_at.desc(), Proposal.id.asc()).offset(offset).limit(page_size)
        items = list(self.session.scalars(stmt).all())
        return items, total

    def update_status(self, proposal: Proposal, status: str) -> Proposal:
        """Update proposal lifecycle status."""
        proposal.status = status
        self.session.flush()
        return proposal

    def update(
        self,
        proposal: Proposal,
        title: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Proposal:
        """Update proposal fields."""
        if title is not None:
            proposal.title = title
        if status is not None:
            proposal.status = status
        self.session.flush()
        return proposal
