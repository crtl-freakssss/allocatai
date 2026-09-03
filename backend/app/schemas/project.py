from pydantic import BaseModel, Field
from app.schemas.enums import ProjectSector
from app.schemas.geography import Geography
from app.schemas.beneficiary import BeneficiaryProfile
from app.schemas.financials import Financials
from app.schemas.impact import ImpactMetric


class Project(BaseModel):
    """Canonical CSR project domain model per AllocateAI technical contract."""

    project_id: str = Field(..., description="Public project identifier, e.g. PRJ-0001")
    name: str = Field(..., min_length=1, max_length=500, description="Project title")
    ngo_id: str = Field(..., description="Implementing partner NGO identifier")
    sector: ProjectSector = Field(..., description="Primary CSR sector")
    geographies: list[Geography] = Field(..., description="Target implementation geographies")
    beneficiary_profile: BeneficiaryProfile = Field(..., description="Target beneficiary demographics")
    financials: Financials = Field(..., description="Project financial parameters in paise")
    duration_months: int = Field(..., gt=0, description="Project duration in months")
    impact_metrics: list[ImpactMetric] = Field(default_factory=list, description="Target impact indicators")
    description: str | None = Field(default=None, description="Detailed project description")
    schema_version: str = Field(default="project-v1", description="Project contract schema version")


class CreateProjectRequest(BaseModel):
    """API request payload for creating a project."""

    name: str = Field(..., min_length=1, max_length=500)
    ngo_id: str
    proposal_id: str | None = None
    sector: ProjectSector
    geographies: list[Geography]
    beneficiary_profile: BeneficiaryProfile
    financials: Financials
    duration_months: int = Field(..., gt=0)
    impact_metrics: list[ImpactMetric] = Field(default_factory=list)
    description: str | None = None


class ProjectResponse(BaseModel):
    """API response payload representing a project."""

    project_id: str
    proposal_id: str | None = None
    ngo_id: str
    name: str
    sector: ProjectSector
    geographies: list[Geography]
    beneficiary_profile: BeneficiaryProfile
    financials: Financials
    duration_months: int
    impact_metrics: list[ImpactMetric] = Field(default_factory=list)
    description: str | None = None
    schema_version: str = "project-v1"
    created_at: str | None = None
    updated_at: str | None = None
