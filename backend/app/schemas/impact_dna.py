from pydantic import BaseModel, Field


class ImpactDNA(BaseModel):
    """Extracted and calculated Impact DNA profile for a project.

    These scores are AI-derived inputs and evidence representations.
    They do not represent final allocation decisions.
    """

    dna_id: str = Field(..., description="Public identifier, e.g. DNA-0001")
    project_id: str = Field(..., description="Referenced project public ID, e.g. PRJ-0001")

    need_score: float = Field(..., ge=0, le=1, description="Local socioeconomic urgency score [0, 1]")
    expected_impact_score: float = Field(..., ge=0, le=1, description="Expected outcome delivery score [0, 1]")
    cost_efficiency_score: float = Field(..., ge=0, le=1, description="Cost per beneficiary efficiency score [0, 1]")
    evidence_strength_score: float = Field(..., ge=0, le=1, description="Robustness of verifiable evidence [0, 1]")
    scalability_score: float = Field(..., ge=0, le=1, description="Replicability and scalability potential [0, 1]")
    implementation_risk_score: float = Field(..., ge=0, le=1, description="Execution and organizational risk score [0, 1]")

    beneficiary_reach: int = Field(..., ge=0, description="Estimated direct beneficiary count")
    estimated_impact_per_lakh: float = Field(..., ge=0, description="Normalized impact output per ₹1,00,000 (10,000,000 paise)")

    missing_fields: list[str] = Field(default_factory=list, description="List of unprovided but required fields")
    extraction_confidence: float = Field(..., ge=0, le=1, description="Confidence in extraction accuracy [0, 1]")

    model_name: str = Field(..., description="Extraction model identifier, e.g. gemini-1.5-pro")
    prompt_version: str = Field(..., description="Prompt template version tag")
    schema_version: str = Field(default="dna-v1", description="DNA contract schema version")
