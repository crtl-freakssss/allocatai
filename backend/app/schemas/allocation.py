from pydantic import BaseModel, Field
from app.schemas.enums import AllocationStatus, ReasonCode


class Allocation(BaseModel):
    """Project-level allocation decision within an optimization run."""

    project_id: str = Field(..., description="Referenced project public ID, e.g. PRJ-0001")
    allocated_amount_paise: int = Field(..., ge=0, strict=True, description="Allocated capital in paise")

    marginal_impact_score: float = Field(..., ge=0, le=1, description="Marginal impact utility score [0, 1]")
    base_score: float = Field(..., ge=0, le=1, description="Base multidimensional project score [0, 1]")
    saturation_index: float = Field(..., ge=0, le=1, description="Regional saturation index [0, 1]")

    reason_codes: list[ReasonCode] = Field(..., description="Audit justification codes for allocation decision")
    rank: int = Field(..., gt=0, description="Priority rank assigned by the solver (1 = highest priority)")

    status: AllocationStatus = Field(default=AllocationStatus.PROPOSED, description="Allocation review status")
