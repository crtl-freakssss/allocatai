from pydantic import BaseModel, Field
from app.schemas.enums import VerificationStatus


class EvidenceItem(BaseModel):
    """Specific claim and ground-truth evidence extracted from proposal artifacts.

    Important: LLM-generated claims are unverified until cross-referenced
    against ground-truth registry or documentation.
    """

    evidence_id: str = Field(..., description="Evidence identifier")
    source_type: str = Field(..., description="Document type or external source")
    source_reference: str | None = Field(default=None, description="Page number, section, or document identifier")
    claim: str = Field(..., description="Extracted claim or factual assertion")
    extracted_value: str | None = Field(default=None, description="Quantitative or qualitative datum extracted")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in extraction accuracy [0, 1]")
    verification_status: VerificationStatus = Field(
        ...,
        description="Verification state of this claim against authoritative records",
    )
