import uuid
from typing import Optional, Tuple, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.ngo import NGO
from app.repositories.base import BaseRepository


class NGORepository(BaseRepository[NGO]):
    """Data access repository for NGO entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, NGO)

    def create(
        self,
        name: str,
        external_id: Optional[str] = None,
        registration_number: Optional[str] = None,
    ) -> NGO:
        """Create and persist a new NGO partner record."""
        ngo = NGO(
            name=name,
            external_id=external_id,
            registration_number=registration_number,
        )
        return self.add(ngo, flush=True)

    def get_by_external_id(self, external_id: str) -> Optional[NGO]:
        """Fetch NGO by unique indexed external identifier."""
        stmt = select(NGO).where(NGO.external_id == external_id)
        return self.session.scalar(stmt)

    def list(self, page: int = 1, page_size: int = 20) -> Tuple[List[NGO], int]:
        """List NGOs with deterministic pagination."""
        offset = max(0, (page - 1) * page_size)
        total_stmt = select(func.count()).select_from(NGO)
        total = self.session.scalar(total_stmt) or 0

        stmt = (
            select(NGO)
            .order_by(NGO.created_at.desc(), NGO.id.asc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(self.session.scalars(stmt).all())
        return items, total

    def update(
        self,
        ngo: NGO,
        name: Optional[str] = None,
        registration_number: Optional[str] = None,
    ) -> NGO:
        """Update NGO details."""
        if name is not None:
            ngo.name = name
        if registration_number is not None:
            ngo.registration_number = registration_number
        self.session.flush()
        return ngo
