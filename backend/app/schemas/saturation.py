from pydantic import BaseModel, Field
from app.schemas.enums import ProjectSector


class SaturationResult(BaseModel):
    """Regional funding and demographic saturation assessment.

    The optimizer utilizes the numeric saturation_index [0, 1] for marginal calculations.
    """

    project_id: str = Field(..., description="Referenced project public ID, e.g. PRJ-0001")
    state: str = Field(..., min_length=1, max_length=100, description="Target state/region")
    sector: ProjectSector = Field(..., description="Target project sector")

    saturation_index: float = Field(..., ge=0, le=1, description="Normalized saturation index [0, 1]")
    need_score: float = Field(..., ge=0, le=1, description="Regional need urgency score [0, 1]")

    existing_csr_amount_paise: int = Field(..., ge=0, strict=True, description="Existing CSR deployment in paise")
    estimated_beneficiary_coverage: float = Field(..., ge=0, le=1, description="Beneficiary saturation ratio [0, 1]")

    confidence: float = Field(..., ge=0, le=1, description="Confidence in regional saturation data [0, 1]")

    calculation_version: str = Field(default="saturation-v1", description="Saturation engine calculation version")
