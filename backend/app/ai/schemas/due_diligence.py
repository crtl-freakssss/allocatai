from typing import List, Optional
from pydantic import BaseModel, Field


class AIDueDiligenceCheckDTO(BaseModel):
    """Statutory check item produced by AI Due Diligence evaluator."""

    check_name: str = Field(..., description="Check category")
    status: str = Field(..., description="VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, MISSING, FLAGGED")
    source: str = Field(..., description="Source verification register")
    evidence: str = Field(..., description="Evidence summary statement")
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)


class AIDueDiligenceDTO(BaseModel):
    """Structured LLM Due Diligence risk report payload."""

    overall_status: str = Field(default="VERIFIED")
    risk_level: str = Field(default="LOW")
    checks: List[AIDueDiligenceCheckDTO] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)
    missing_documents: List[str] = Field(default_factory=list)
