from pydantic import BaseModel, Field


class ImpactMetric(BaseModel):
    """Specific quantifiable impact target and measurement method."""

    metric_id: str = Field(..., description="Unique impact metric identifier")
    name: str = Field(..., description="Human-readable impact metric name")
    unit: str = Field(..., description="Unit of measurement (e.g. students, liters, trees)")
    baseline: float | None = Field(default=None, description="Pre-intervention baseline value")
    target: float | None = Field(default=None, description="Target post-intervention value")
    measurement_method: str | None = Field(default=None, description="Data collection and evaluation methodology")
