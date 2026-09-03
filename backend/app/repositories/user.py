import uuid
from typing import Optional, Tuple, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access repository for User entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, User)

    def create(
        self,
        email: str,
        organization_id: Optional[uuid.UUID] = None,
        name: Optional[str] = None,
    ) -> User:
        """Create and persist a new user record."""
        user = User(
            email=email.strip().lower(),
            organization_id=organization_id,
            name=name,
        )
        return self.add(user, flush=True)

    def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by unique indexed email address."""
        stmt = select(User).where(User.email == email.strip().lower())
        return self.session.scalar(stmt)

    def exists_by_email(self, email: str) -> bool:
        """Check whether a user with the given email address already exists."""
        stmt = select(func.count()).select_from(User).where(User.email == email.strip().lower())
        count = self.session.scalar(stmt) or 0
        return count > 0

    def list_by_organization(
        self,
        organization_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[User], int]:
        """List users belonging to a specific organization with deterministic pagination."""
        offset = max(0, (page - 1) * page_size)
        total_stmt = (
            select(func.count())
            .select_from(User)
            .where(User.organization_id == organization_id)
        )
        total = self.session.scalar(total_stmt) or 0

        stmt = (
            select(User)
            .where(User.organization_id == organization_id)
            .order_by(User.created_at.desc(), User.id.asc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(self.session.scalars(stmt).all())
        return items, total

    def update(
        self,
        user: User,
        name: Optional[str] = None,
        organization_id: Optional[uuid.UUID] = None,
    ) -> User:
        """Update user profile or organization affiliation."""
        if name is not None:
            user.name = name
        if organization_id is not None:
            user.organization_id = organization_id
        self.session.flush()
        return user
