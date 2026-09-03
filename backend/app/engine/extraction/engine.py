from typing import Optional
from app.schemas.extraction import ExtractionResult
from app.ai.extraction import AIExtractor


class RealExtractionEngine:
    """Production extraction engine delegating document text parsing and structured extraction to Person 2's AIExtractor."""

    def __init__(self, extractor: Optional[AIExtractor] = None) -> None:
        self.extractor = extractor or AIExtractor()

    def extract(
        self,
        proposal_id: str,
        document_id: str,
        filename: str,
        mime_type: str,
        storage_key: str,
    ) -> ExtractionResult:
        """Parse proposal document text and extract structured project attributes."""
        extraction_result, _ = self.extractor.extract(
            document_path_or_text=storage_key,
            filename=filename,
            proposal_public_id=proposal_id,
            document_public_id=document_id,
        )
        extraction_result.proposal_id = proposal_id
        extraction_result.document_id = document_id
        return extraction_result
