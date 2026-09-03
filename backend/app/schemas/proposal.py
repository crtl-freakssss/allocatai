from pydantic import BaseModel, Field
from app.schemas.enums import ProposalStatus


class CreateProposalRequest(BaseModel):
    """API request payload to register a new proposal."""

    ngo_id: str = Field(..., description="Implementing partner NGO identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Proposal title")
    source_type: str = Field(default="DIRECT_SUBMISSION", max_length=50, description="Channel of receipt")


class CreateProposalResponse(BaseModel):
    """API response acknowledging proposal registration."""

    proposal_id: str = Field(..., description="Public proposal identifier, e.g. PRO-0001")
    status: ProposalStatus = Field(default=ProposalStatus.UPLOADED, description="Initial proposal status")


class ProposalResponse(BaseModel):
    """API representation of an ingested proposal."""

    proposal_id: str = Field(..., description="Public proposal identifier, e.g. PRO-0001")
    ngo_id: str = Field(..., description="Implementing partner NGO identifier")
    title: str = Field(..., description="Proposal title")
    status: ProposalStatus = Field(..., description="Current proposal lifecycle status")
    source_type: str = Field(..., description="Channel of receipt")
    created_at: str = Field(..., description="UTC ISO timestamp of registration")
    updated_at: str | None = Field(default=None, description="UTC ISO timestamp of latest update")


class ExtractProposalRequest(BaseModel):
    """API request to trigger automated extraction on an uploaded proposal document."""

    document_id: str = Field(..., description="Public document identifier to extract from, e.g. DOC-0001")


class ExtractProposalResponse(BaseModel):
    """API response summarizing automated proposal extraction results."""

    proposal_id: str = Field(..., description="Public proposal identifier, e.g. PRO-0001")
    status: ProposalStatus = Field(..., description="Updated proposal status (e.g. EXTRACTED or VALIDATION_REQUIRED)")
    project_id: str | None = Field(default=None, description="Created project public ID if successfully extracted, e.g. PRJ-0001")
    extraction_confidence: float = Field(..., ge=0, le=1, description="Aggregate extraction confidence score [0, 1]")
    missing_fields: list[str] = Field(default_factory=list, description="Fields required by contract but missing from source")
