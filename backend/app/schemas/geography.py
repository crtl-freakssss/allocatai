from pydantic import BaseModel, Field


class Geography(BaseModel):
    """Geographical targeting model for a project."""

    state: str = Field(..., min_length=1, max_length=100, description="State or union territory name")
    district: str | None = Field(default=None, max_length=100, description="District name")
    block: str | None = Field(default=None, max_length=100, description="Block or taluk name")
