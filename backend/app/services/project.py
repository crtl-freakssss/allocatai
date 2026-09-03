import uuid
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.project import Project
from app.repositories.project import ProjectRepository
from app.repositories.ngo import NGORepository
from app.repositories.proposal import ProposalRepository
from app.services.audit import AuditService
from app.services.exceptions import (
    ResourceNotFoundError,
    ServiceValidationError,
)
from app.schemas.enums import AuditEventType, ProjectSector
from app.db.identifiers import generate_public_id


class ProjectService:
    """Service orchestrating CSR project lifecycle, geographic scoping, and auditing."""

    def __init__(
        self,
        session: Session,
        project_repository: Optional[ProjectRepository] = None,
        ngo_repository: Optional[NGORepository] = None,
        proposal_repository: Optional[ProposalRepository] = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        self.session = session
        self.project_repo = project_repository or ProjectRepository(session)
        self.ngo_repo = ngo_repository or NGORepository(session)
        self.proposal_repo = proposal_repository or ProposalRepository(session)
        self.audit_service = audit_service or AuditService(session)

    def create_project(
        self,
        ngo_id: uuid.UUID,
        name: str,
        sector: ProjectSector | str,
        duration_months: int,
        requested_amount_paise: int,
        geographies: List[Dict[str, Any]],
        current_funding_paise: int = 0,
        proposal_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        schema_version: str = "v1",
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> Project:
        """Atomically validate references, generate authoritative PRJ ID, and persist project with geographies."""
        if not name or not name.strip():
            raise ServiceValidationError("Project name cannot be empty", field="name")
        if duration_months <= 0:
            raise ServiceValidationError("Duration months must be strictly greater than zero", field="duration_months")
        if requested_amount_paise <= 0:
            raise ServiceValidationError("Requested amount in paise must be strictly greater than zero", field="requested_amount_paise")
        if current_funding_paise < 0:
            raise ServiceValidationError("Current funding in paise cannot be negative", field="current_funding_paise")
        if not geographies:
            raise ServiceValidationError("At least one target geography must be specified", field="geographies")

        if not self.ngo_repo.exists(ngo_id):
            raise ResourceNotFoundError("NGO", ngo_id)

        if proposal_id is not None and not self.proposal_repo.exists(proposal_id):
            raise ResourceNotFoundError("Proposal", proposal_id)

        sector_str = sector.value if isinstance(sector, ProjectSector) else str(sector)

        try:
            stmt = select(func.count()).select_from(Project)
            count = self.session.scalar(stmt) or 0
            public_id = generate_public_id("PRJ", count + 1)

            project = self.project_repo.create(
                public_id=public_id,
                ngo_id=ngo_id,
                name=name.strip(),
                sector=sector_str,
                duration_months=duration_months,
                requested_amount=requested_amount_paise,
                current_funding=current_funding_paise,
                proposal_id=proposal_id,
                description=description,
                schema_version=schema_version,
            )

            for geo in geographies:
                state = geo.get("state")
                if not state or not state.strip():
                    raise ServiceValidationError("Geography state must not be empty", field="geographies.state")
                self.project_repo.add_geography(
                    project_id=project.id,
                    state=state.strip(),
                    district=geo.get("district"),
                    block=geo.get("block"),
                )

            self.audit_service.record_event(
                event_type=AuditEventType.PROJECT_CREATED,
                payload={
                    "public_id": public_id,
                    "name": project.name,
                    "sector": project.sector,
                    "requested_amount": requested_amount_paise,
                },
                entity_type="projects",
                entity_id=project.id,
                actor_id=actor_id,
                request_id=request_id,
            )

            self.session.commit()
            return project
        except Exception:
            self.session.rollback()
            raise

    def get_project(self, public_id: str) -> Project:
        """Fetch project by public ID or raise ResourceNotFoundError."""
        project = self.project_repo.get_by_public_id(public_id)
        if not project:
            raise ResourceNotFoundError("Project", public_id)
        return project

    def list_projects(
        self,
        ngo_id: Optional[uuid.UUID] = None,
        proposal_id: Optional[uuid.UUID] = None,
        sector: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Project], int]:
        """List projects with deterministic pagination."""
        return self.project_repo.list(
            ngo_id=ngo_id,
            proposal_id=proposal_id,
            sector=sector,
            page=page,
            page_size=page_size,
        )

    def update_project(
        self,
        public_id: str,
        name: Optional[str] = None,
        current_funding: Optional[int] = None,
        description: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> Project:
        """Atomically update project details."""
        project = self.get_project(public_id)
        try:
            self.project_repo.update(
                project=project,
                name=name,
                current_funding=current_funding,
                description=description,
            )
            self.audit_service.record_event(
                event_type="PROJECT_UPDATED",
                payload={"public_id": public_id, "current_funding": current_funding},
                entity_type="projects",
                entity_id=project.id,
                actor_id=actor_id,
                request_id=request_id,
            )
            self.session.commit()
            return project
        except Exception:
            self.session.rollback()
            raise
