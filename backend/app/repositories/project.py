import uuid
from typing import Optional, Tuple, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.project_geography import ProjectGeography
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Data access repository for Project entities and related geographies."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Project)

    def create(
        self,
        public_id: str,
        ngo_id: uuid.UUID,
        name: str,
        sector: str,
        duration_months: int,
        requested_amount: int,
        current_funding: int = 0,
        proposal_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        schema_version: str = "v1",
    ) -> Project:
        """Create and persist a new CSR project record."""
        project = Project(
            public_id=public_id,
            ngo_id=ngo_id,
            name=name,
            sector=sector,
            duration_months=duration_months,
            requested_amount=requested_amount,
            current_funding=current_funding,
            proposal_id=proposal_id,
            description=description,
            schema_version=schema_version,
        )
        return self.add(project, flush=True)

    def add_geography(
        self,
        project_id: uuid.UUID,
        state: str,
        district: Optional[str] = None,
        block: Optional[str] = None,
    ) -> ProjectGeography:
        """Add a single geographic target boundary to a project."""
        geo = ProjectGeography(
            project_id=project_id,
            state=state,
            district=district,
            block=block,
        )
        self.session.add(geo)
        self.session.flush()
        return geo

    def add_geographies(
        self,
        geographies: List[ProjectGeography],
    ) -> List[ProjectGeography]:
        """Bulk add multiple geographic boundaries to projects."""
        for geo in geographies:
            self.session.add(geo)
        self.session.flush()
        return geographies

    def get_by_public_id(self, public_id: str) -> Optional[Project]:
        """Fetch project by authoritative public identifier (e.g. PRJ-0001)."""
        stmt = select(Project).where(Project.public_id == public_id)
        return self.session.scalar(stmt)

    def exists_by_public_id(self, public_id: str) -> bool:
        """Check whether a project with the given public ID exists."""
        stmt = select(func.count()).select_from(Project).where(Project.public_id == public_id)
        count = self.session.scalar(stmt) or 0
        return count > 0

    def list(
        self,
        ngo_id: Optional[uuid.UUID] = None,
        proposal_id: Optional[uuid.UUID] = None,
        sector: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Project], int]:
        """List projects with deterministic pagination and optional filters."""
        offset = max(0, (page - 1) * page_size)

        filters = []
        if ngo_id is not None:
            filters.append(Project.ngo_id == ngo_id)
        if proposal_id is not None:
            filters.append(Project.proposal_id == proposal_id)
        if sector is not None:
            filters.append(Project.sector == sector)

        total_stmt = select(func.count()).select_from(Project)
        if filters:
            total_stmt = total_stmt.where(*filters)
        total = self.session.scalar(total_stmt) or 0

        stmt = select(Project)
        if filters:
            stmt = stmt.where(*filters)

        stmt = stmt.order_by(Project.created_at.desc(), Project.id.asc()).offset(offset).limit(page_size)
        items = list(self.session.scalars(stmt).all())
        return items, total

    def get_by_ngo(self, ngo_id: uuid.UUID) -> List[Project]:
        """List all projects associated with a given NGO."""
        stmt = select(Project).where(Project.ngo_id == ngo_id).order_by(Project.created_at.desc(), Project.id.asc())
        return list(self.session.scalars(stmt).all())

    def get_by_proposal(self, proposal_id: uuid.UUID) -> List[Project]:
        """List all projects originating from a given proposal."""
        stmt = select(Project).where(Project.proposal_id == proposal_id).order_by(Project.created_at.desc(), Project.id.asc())
        return list(self.session.scalars(stmt).all())

    def update(
        self,
        project: Project,
        name: Optional[str] = None,
        current_funding: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Project:
        """Update project details."""
        if name is not None:
            project.name = name
        if current_funding is not None:
            project.current_funding = current_funding
        if description is not None:
            project.description = description
        self.session.flush()
        return project
