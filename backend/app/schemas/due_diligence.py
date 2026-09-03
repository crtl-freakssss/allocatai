from pydantic import BaseModel, Field
from app.schemas.enums import DueDiligenceRisk, VerificationStatus

DEFAULT_DISCLAIMER: str = (
    "This report is an evidence and risk-assessment layer "
    "and does not constitute legal or regulatory certification."
)


class DueDiligenceCheck(BaseModel):
    """Specific automated compliance or verification check result."""

    check_name: str = Field(..., description="Check identifier (e.g. fcra_validity, 12a_80g_compliance)")
    status: VerificationStatus = Field(..., description="Verification finding status")
    source: str | None = Field(default=None, description="Source registry or document evaluated")
    evidence: str | None = Field(default=None, description="Snippet or verifiable evidence reference")
    confidence: float = Field(default=0.0, ge=0, le=1, description="Verification confidence score [0, 1]")
    checked_at: str = Field(..., description="UTC ISO timestamp of verification check")


class DueDiligenceReport(BaseModel):
    """Comprehensive NGO risk assessment and governance audit report.

    Important: This layer provides evidence aggregation and risk indicators.
    It does not constitute legal certification.
    """

    report_id: str = Field(..., description="Public identifier, e.g. DD-0001")
    ngo_id: str = Field(..., description="Target NGO identifier")

    overall_status: VerificationStatus = Field(..., description="Aggregate verification status")
    risk_level: DueDiligenceRisk = Field(..., description="Assessed NGO risk category")

    checks: list[DueDiligenceCheck] = Field(..., description="Itemized compliance check findings")

    flags: list[str] = Field(default_factory=list, description="Elevated risk markers or audit red flags")
    missing_documents: list[str] = Field(default_factory=list, description="List of required but unsupplied filings")

    model_name: str | None = Field(default=None, description="LLM/evaluator model tag")
    model_version: str = Field(default="due-diligence-v1", description="Due diligence pipeline version")

    disclaimer: str = Field(
        default=DEFAULT_DISCLAIMER,
        description="Mandatory legal disclaimer clarifying non-certification role",
    )
