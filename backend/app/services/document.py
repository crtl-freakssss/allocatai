import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.document import Document
from app.repositories.document import DocumentRepository
from app.repositories.proposal import ProposalRepository
from app.services.audit import AuditService
from app.services.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    ServiceValidationError,
)
from app.schemas.enums import AuditEventType
from app.db.identifiers import generate_public_id


class DocumentService:
    """Service orchestrating proposal document attachment metadata and deduplication."""

    def __init__(
        self,
        session: Session,
        document_repository: Optional[DocumentRepository] = None,
        proposal_repository: Optional[ProposalRepository] = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        self.session = session
        self.document_repo = document_repository or DocumentRepository(session)
        self.proposal_repo = proposal_repository or ProposalRepository(session)
        self.audit_service = audit_service or AuditService(session)

    def attach_document(
        self,
        proposal_public_id: str,
        filename: str,
        mime_type: str,
        storage_key: str,
        file_size_bytes: int,
        sha256: str,
        actor_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> Document:
        """Atomically attach document metadata to an existing proposal."""
        if not filename or not filename.strip():
            raise ServiceValidationError("Filename cannot be empty", field="filename")
        if file_size_bytes <= 0:
            raise ServiceValidationError("File size must be greater than zero", field="file_size_bytes")
        clean_sha = sha256.lower().strip()
        if not clean_sha or len(clean_sha) != 64:
            raise ServiceValidationError("Valid 64-character SHA-256 hash required", field="sha256")

        proposal = self.proposal_repo.get_by_public_id(proposal_public_id)
        if not proposal:
            raise ResourceNotFoundError("Proposal", proposal_public_id)

        # Check for duplicate document on this proposal
        existing = self.document_repo.get_by_proposal_and_sha256(proposal.id, clean_sha)
        if existing:
            raise ResourceAlreadyExistsError("Document", "sha256", clean_sha, "Identical document already attached to this proposal")

        try:
            stmt = select(func.count()).select_from(Document)
            count = self.session.scalar(stmt) or 0
            public_id = generate_public_id("DOC", count + 1)

            doc = self.document_repo.create(
                public_id=public_id,
                proposal_id=proposal.id,
                filename=filename.strip(),
                mime_type=mime_type.strip(),
                storage_key=storage_key.strip(),
                file_size_bytes=file_size_bytes,
                sha256=sha256.lower().strip(),
            )

            self.audit_service.record_event(
                event_type=AuditEventType.DOCUMENT_UPLOADED,
                payload={
                    "public_id": public_id,
                    "proposal_id": proposal_public_id,
                    "filename": filename,
                    "file_size_bytes": file_size_bytes,
                },
                entity_type="documents",
                entity_id=doc.id,
                actor_id=actor_id,
                request_id=request_id,
            )

            self.session.commit()
            return doc
        except Exception:
            self.session.rollback()
            raise

    def get_document(self, public_id: str) -> Document:
        """Fetch document by public ID or raise ResourceNotFoundError."""
        doc = self.document_repo.get_by_public_id(public_id)
        if not doc:
            raise ResourceNotFoundError("Document", public_id)
        return doc

    def list_proposal_documents(self, proposal_public_id: str) -> List[Document]:
        """List all documents attached to a given proposal."""
        proposal = self.proposal_repo.get_by_public_id(proposal_public_id)
        if not proposal:
            raise ResourceNotFoundError("Proposal", proposal_public_id)
        return self.document_repo.get_by_proposal(proposal.id)
