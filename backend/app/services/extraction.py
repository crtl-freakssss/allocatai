import uuid
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.project import Project
from app.repositories.proposal import ProposalRepository
from app.repositories.document import DocumentRepository
from app.repositories.project import ProjectRepository
from app.services.audit import AuditService
from app.services.interfaces import ExtractionEngine
from app.services.exceptions import (
    ResourceNotFoundError,
    ConflictError,
    ProcessingError,
)
from app.schemas.enums import ProposalStatus, AuditEventType
from app.schemas.extraction import ExtractionResult
from app.db.identifiers import generate_public_id


class ExtractionService:
    """Service orchestrating AI-driven proposal extraction and project persistence."""

    def __init__(
        self,
        session: Session,
        proposal_repository: Optional[ProposalRepository] = None,
        document_repository: Optional[DocumentRepository] = None,
        project_repository: Optional[ProjectRepository] = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        self.session = session
        self.proposal_repo = proposal_repository or ProposalRepository(session)
        self.document_repo = document_repository or DocumentRepository(session)
        self.project_repo = project_repository or ProjectRepository(session)
        self.audit_service = audit_service or AuditService(session)

    def extract_proposal(
        self,
        proposal_public_id: str,
        document_public_id: str,
        engine: ExtractionEngine,
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> Tuple[ExtractionResult, Project]:
        """Orchestrate end-to-end extraction, authoritative project ID assignment, and persistence."""
        proposal = self.proposal_repo.get_by_public_id(proposal_public_id)
        if not proposal:
            raise ResourceNotFoundError("Proposal", proposal_public_id)

        document = self.document_repo.get_by_public_id(document_public_id)
        if not document:
            raise ResourceNotFoundError("Document", document_public_id)

        # Cross-entity boundary check: verify document belongs to proposal
        if document.proposal_id != proposal.id:
            raise ConflictError(
                f"Document '{document_public_id}' is not associated with proposal '{proposal_public_id}'"
            )

        try:
            # Audit start of extraction
            self.audit_service.record_event(
                event_type=AuditEventType.EXTRACTION_STARTED,
                payload={"proposal_id": proposal_public_id, "document_id": document_public_id},
                entity_type="proposals",
                entity_id=proposal.id,
                actor_id=actor_id,
                request_id=request_id,
            )

            # Invoke extraction engine interface
            try:
                extraction_result = engine.extract(
                    proposal_id=proposal_public_id,
                    document_id=document_public_id,
                    filename=document.filename,
                    mime_type=document.mime_type,
                    storage_key=document.storage_key,
                )
            except Exception as e:
                raise ProcessingError(f"Extraction engine failed: {str(e)}", cause=e)

            # The backend owns persistent IDs - generate official PRJ ID
            stmt = select(func.count()).select_from(Project)
            count = self.session.scalar(stmt) or 0
            official_project_id = generate_public_id("PRJ", count + 1)

            extracted_data = extraction_result.extracted_project

            # Persist project with backend-authoritative public ID
            project = self.project_repo.create(
                public_id=official_project_id,
                ngo_id=proposal.ngo_id,
                name=extracted_data.name,
                sector=extracted_data.sector.value,
                duration_months=extracted_data.duration_months,
                requested_amount=extracted_data.financials.requested_amount_paise,
                current_funding=extracted_data.financials.current_funding_paise,
                proposal_id=proposal.id,
                description=extracted_data.description,
                schema_version=extracted_data.schema_version,
            )

            # Persist extracted geographies
            for geo in extracted_data.geographies:
                self.project_repo.add_geography(
                    project_id=project.id,
                    state=geo.state,
                    district=geo.district,
                    block=geo.block,
                )

            # Update proposal lifecycle status
            new_status = (
                ProposalStatus.VALIDATION_REQUIRED.value
                if extraction_result.missing_fields
                else ProposalStatus.EXTRACTED.value
            )
            proposal.status = new_status
            self.session.flush()

            # Audit extraction completion
            self.audit_service.record_event(
                event_type=AuditEventType.EXTRACTION_COMPLETED,
                payload={
                    "proposal_id": proposal_public_id,
                    "document_id": document_public_id,
                    "project_public_id": official_project_id,
                    "confidence": extraction_result.extraction_confidence,
                    "missing_fields": extraction_result.missing_fields,
                },
                entity_type="projects",
                entity_id=project.id,
                actor_id=actor_id,
                request_id=request_id,
            )

            self.session.commit()
            return extraction_result, project

        except Exception:
            self.session.rollback()
            raise
