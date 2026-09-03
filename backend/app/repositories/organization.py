import uuid
from typing import Optional, Tuple, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Data access repository for Organization entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Organization)

    def create(self, name: str) -> Organization:
        """Create and persist a new organization record."""
        org = Organization(name=name)
        return self.add(org, flush=True)

    def list(self, page: int = 1, page_size: int = 20) -> Tuple[List[Organization], int]:
        """List organizations with deterministic pagination."""
        offset = max(0, (page - 1) * page_size)
        total_stmt = select(func.count()).select_from(Organization)
        total = self.session.scalar(total_stmt) or 0

        stmt = (
            select(Organization)
            .order_by(Organization.created_at.desc(), Organization.id.asc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(self.session.scalars(stmt).all())
        return items, total

    def update(self, org: Organization, name: Optional[str] = None) -> Organization:
        """Update organization details."""
        if name is not None:
            org.name = name
        self.session.flush()
        return org
