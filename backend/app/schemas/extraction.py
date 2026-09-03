from pydantic import BaseModel, Field
from app.schemas.project import Project
from app.schemas.evidence import EvidenceItem


class ExtractionResult(BaseModel):
    """Structured extraction output produced by AI ingestion pipeline."""

    proposal_id: str = Field(..., description="Referenced proposal public ID, e.g. PRO-0001")
    document_id: str = Field(..., description="Referenced document public ID, e.g. DOC-0001")

    extracted_project: Project = Field(..., description="Normalized project entity extracted from document")

    evidence: list[EvidenceItem] = Field(..., description="Extracted claims and citations from document")

    missing_fields: list[str] = Field(..., description="Required contract fields not discoverable in source")
    warnings: list[str] = Field(..., description="Extraction warnings or data anomalies detected")

    extraction_confidence: float = Field(..., ge=0, le=1, description="Aggregate extraction confidence score [0, 1]")

    model_name: str = Field(..., description="AI model tag utilized for extraction")
    prompt_version: str = Field(..., description="Prompt template version tag")
    schema_version: str = Field(default="extraction-v1", description="Extraction contract schema version")
