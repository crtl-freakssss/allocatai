from pydantic import BaseModel, Field
from app.schemas.enums import ProposalStatus


class CreateDocumentResponse(BaseModel):
    """API response acknowledging document upload attachment."""

    document_id: str = Field(..., description="Public document identifier, e.g. DOC-0001")
    proposal_id: str = Field(..., description="Referenced proposal public ID, e.g. PRO-0001")
    filename: str = Field(..., description="Original uploaded filename")
    status: ProposalStatus = Field(default=ProposalStatus.UPLOADED, description="Proposal lifecycle status")


class DocumentResponse(BaseModel):
    """API representation of an uploaded document attachment."""

    document_id: str = Field(..., description="Public document identifier, e.g. DOC-0001")
    proposal_id: str = Field(..., description="Referenced proposal public ID, e.g. PRO-0001")
    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME content type")
    file_size_bytes: int = Field(..., ge=0, strict=True, description="File size in bytes")
    sha256: str = Field(..., description="SHA-256 integrity hash")
    created_at: str = Field(..., description="UTC ISO timestamp of upload")


class UploadDocumentRequest(BaseModel):
    """API request payload to attach document metadata to a proposal."""

    filename: str = Field(..., min_length=1, max_length=255, description="Document filename")
    mime_type: str = Field(default="application/pdf", min_length=1, max_length=100, description="MIME content type")
    storage_key: str = Field(..., min_length=1, max_length=500, description="Storage URI or key")
    file_size_bytes: int = Field(..., gt=0, strict=True, description="File size in bytes")
    sha256: str = Field(..., min_length=64, max_length=64, description="64-character SHA-256 hash")

