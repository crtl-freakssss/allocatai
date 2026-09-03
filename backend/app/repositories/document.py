import uuid
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Data access repository for Document metadata entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Document)

    def create(
        self,
        public_id: str,
        proposal_id: uuid.UUID,
        filename: str,
        mime_type: str,
        storage_key: str,
        file_size_bytes: int,
        sha256: str,
    ) -> Document:
        """Create and persist a document attachment record."""
        doc = Document(
            public_id=public_id,
            proposal_id=proposal_id,
            filename=filename,
            mime_type=mime_type,
            storage_key=storage_key,
            file_size_bytes=file_size_bytes,
            sha256=sha256,
        )
        return self.add(doc, flush=True)

    def get_by_public_id(self, public_id: str) -> Optional[Document]:
        """Fetch document by unique public identifier (e.g. DOC-0001)."""
        stmt = select(Document).where(Document.public_id == public_id)
        return self.session.scalar(stmt)

    def get_by_proposal(self, proposal_id: uuid.UUID) -> List[Document]:
        """Fetch all document records linked to a specific proposal."""
        stmt = (
            select(Document)
            .where(Document.proposal_id == proposal_id)
            .order_by(Document.created_at.asc(), Document.id.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_by_sha256(self, sha256: str) -> Optional[Document]:
        """Fetch document by SHA-256 integrity hash."""
        stmt = select(Document).where(Document.sha256 == sha256)
        return self.session.scalar(stmt)

    def get_by_proposal_and_sha256(self, proposal_id: uuid.UUID, sha256: str) -> Optional[Document]:
        """Fetch document for a specific proposal matching SHA-256 integrity hash."""
        stmt = (
            select(Document)
            .where(Document.proposal_id == proposal_id, Document.sha256 == sha256)
        )
        return self.session.scalar(stmt)

    def exists_by_public_id(self, public_id: str) -> bool:
        """Check whether a document with the given public ID exists."""
        stmt = select(func.count()).select_from(Document).where(Document.public_id == public_id)
        count = self.session.scalar(stmt) or 0
        return count > 0
