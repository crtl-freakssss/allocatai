import uuid
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.proposal import Proposal
from app.repositories.proposal import ProposalRepository
from app.repositories.ngo import NGORepository
from app.services.audit import AuditService
from app.services.exceptions import (
    ResourceNotFoundError,
    InvalidStateTransitionError,
    ServiceValidationError,
)
from app.schemas.enums import ProposalStatus, AuditEventType
from app.db.identifiers import generate_public_id


class ProposalService:
    """Service orchestrating proposal intake, status progression, and auditing."""

    def __init__(
        self,
        session: Session,
        proposal_repository: Optional[ProposalRepository] = None,
        ngo_repository: Optional[NGORepository] = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        self.session = session
        self.proposal_repo = proposal_repository or ProposalRepository(session)
        self.ngo_repo = ngo_repository or NGORepository(session)
        self.audit_service = audit_service or AuditService(session)

    def create_proposal(
        self,
        ngo_id: uuid.UUID,
        title: str,
        source_type: str = "DIRECT_SUBMISSION",
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> Proposal:
        """Atomically validate NGO reference, create proposal, and log audit event."""
        if not title or not title.strip():
            raise ServiceValidationError("Proposal title cannot be empty", field="title")

        if not self.ngo_repo.exists(ngo_id):
            raise ResourceNotFoundError("NGO", ngo_id)

        try:
            # Generate deterministic public identifier
            stmt = select(func.count()).select_from(Proposal)
            count = self.session.scalar(stmt) or 0
            public_id = generate_public_id("PRO", count + 1)

            proposal = self.proposal_repo.create(
                public_id=public_id,
                ngo_id=ngo_id,
                title=title.strip(),
                status=ProposalStatus.UPLOADED.value,
                source_type=source_type,
            )

            # Record audit event
            self.audit_service.record_event(
                event_type=AuditEventType.PROPOSAL_CREATED,
                payload={"public_id": public_id, "title": proposal.title, "ngo_id": str(ngo_id)},
                entity_type="proposals",
                entity_id=proposal.id,
                actor_id=actor_id,
                request_id=request_id,
                run_id=None,
            )

            self.session.commit()
            return proposal
        except Exception:
            self.session.rollback()
            raise

    def get_proposal(self, public_id: str) -> Proposal:
        """Fetch proposal by public ID or raise ResourceNotFoundError."""
        proposal = self.proposal_repo.get_by_public_id(public_id)
        if not proposal:
            raise ResourceNotFoundError("Proposal", public_id)
        return proposal

    def get_proposal_by_id(self, proposal_id: uuid.UUID) -> Proposal:
        """Fetch proposal by internal UUID or raise ResourceNotFoundError."""
        proposal = self.proposal_repo.get_by_id(proposal_id)
        if not proposal:
            raise ResourceNotFoundError("Proposal", proposal_id)
        return proposal

    def list_proposals(
        self,
        ngo_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Proposal], int]:
        """List proposals with deterministic pagination."""
        return self.proposal_repo.list(ngo_id=ngo_id, status=status, page=page, page_size=page_size)

    def update_proposal(
        self,
        public_id: str,
        title: Optional[str] = None,
        status: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> Proposal:
        """Atomically update proposal attributes with transition validation."""
        proposal = self.get_proposal(public_id)

        try:
            if status is not None and status != proposal.status:
                # Disallow transitions from terminal states
                if proposal.status in (ProposalStatus.REJECTED.value, ProposalStatus.FAILED.value):
                    raise InvalidStateTransitionError(
                        entity_type="Proposal",
                        current_state=proposal.status,
                        target_state=status,
                    )
                proposal.status = status

            if title is not None and title.strip():
                proposal.title = title.strip()

            self.session.flush()

            self.audit_service.record_event(
                event_type="PROPOSAL_UPDATED",
                payload={"public_id": public_id, "status": proposal.status, "title": proposal.title},
                entity_type="proposals",
                entity_id=proposal.id,
                actor_id=actor_id,
                request_id=request_id,
            )

            self.session.commit()
            return proposal
        except Exception:
            self.session.rollback()
            raise
