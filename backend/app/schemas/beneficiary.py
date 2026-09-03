from pydantic import BaseModel, Field


class BeneficiaryProfile(BaseModel):
    """Target beneficiary demographics and reach estimates."""

    target_count: int = Field(..., ge=0, description="Estimated count of targeted beneficiaries")
    groups: list[str] = Field(default_factory=list, description="Target groups (e.g. farmers, students)")
    age_ranges: list[str] = Field(default_factory=list, description="Target age brackets (e.g. 6-14, 18-35)")
    vulnerable_groups: list[str] = Field(default_factory=list, description="Vulnerable demographic groups targeted")
