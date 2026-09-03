from typing import List, Optional
from pydantic import BaseModel, Field


class AIEvidenceDTO(BaseModel):
    """AI extraction evidence claim item."""

    source_reference: str = Field(..., description="Section or page reference in document")
    claim: str = Field(..., description="Extracted claim text")
    extracted_value: str = Field(..., description="Extracted numerical or categorical fact")
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)


class AIExtractionDTO(BaseModel):
    """Structured LLM extraction payload."""

    project_name: str = Field(..., description="Extracted project title")
    sector: str = Field(..., description="Project sector (e.g. EDUCATION, HEALTHCARE, ENVIRONMENT)")
    state: str = Field(..., description="Target Indian state")
    district: Optional[str] = Field(default=None, description="Target district")
    block: Optional[str] = Field(default=None, description="Target administrative block")
    requested_amount_paise: int = Field(..., gt=0, description="Requested budget in paise")
    target_beneficiary_count: int = Field(default=2000, ge=1)
    duration_months: int = Field(default=12, ge=1)
    description: str = Field(..., description="Project summary description")
    evidence: List[AIEvidenceDTO] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    extraction_confidence: float = Field(default=0.92, ge=0.0, le=1.0)
