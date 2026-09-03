from typing import List
from pydantic import BaseModel, Field


class AIImpactDNADTO(BaseModel):
    """Structured LLM Impact DNA evaluation payload."""

    need_score: float = Field(..., ge=0.0, le=1.0)
    expected_impact_score: float = Field(..., ge=0.0, le=1.0)
    cost_efficiency_score: float = Field(..., ge=0.0, le=1.0)
    evidence_strength_score: float = Field(..., ge=0.0, le=1.0)
    scalability_score: float = Field(..., ge=0.0, le=1.0)
    implementation_risk_score: float = Field(..., ge=0.0, le=1.0)
    beneficiary_reach: int = Field(..., ge=0)
    estimated_impact_per_lakh: float = Field(..., ge=0.0)
    missing_fields: List[str] = Field(default_factory=list)
    extraction_confidence: float = Field(default=0.92, ge=0.0, le=1.0)
