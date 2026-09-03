from typing import Tuple, Optional, List
from app.ai.client import LLMClient
from app.ai.extraction import AIExtractor
from app.ai.impact_dna import AIImpactDNAGenerator
from app.ai.due_diligence import AIDueDiligenceEvaluator
from app.schemas.extraction import ExtractionResult
from app.schemas.project import Project as SchemaProject
from app.schemas.impact_dna import ImpactDNA as SchemaImpactDNA
from app.schemas.due_diligence import DueDiligenceReport


class AIPipeline:
    """Unified AI Pipeline facade coordinating document extraction, Impact DNA evaluation, and statutory Due Diligence."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.client = llm_client or LLMClient()
        self.extractor = AIExtractor(llm_client=self.client)
        self.impact_dna_generator = AIImpactDNAGenerator(llm_client=self.client)
        self.due_diligence_evaluator = AIDueDiligenceEvaluator(llm_client=self.client)

    def extract_proposal(
        self,
        document_path_or_text: str,
        filename: str = "proposal.pdf",
        proposal_public_id: str = "PRO-0000",
        ngo_id: str = "NGO-0000",
    ) -> Tuple[ExtractionResult, SchemaProject]:
        """Orchestrate proposal document extraction."""
        return self.extractor.extract(
            document_path_or_text=document_path_or_text,
            filename=filename,
            proposal_public_id=proposal_public_id,
            ngo_id=ngo_id,
        )

    def generate_impact_dna(
        self,
        project: SchemaProject,
        project_public_id: str = "PRJ-0000",
    ) -> SchemaImpactDNA:
        """Orchestrate Impact DNA dimension evaluation."""
        return self.impact_dna_generator.generate_impact_dna(
            project=project,
            project_public_id=project_public_id,
        )

    def evaluate_due_diligence(
        self,
        ngo_name: str,
        registration_number: Optional[str] = None,
        external_id: Optional[str] = None,
        document_filenames: Optional[List[str]] = None,
        ngo_public_id: str = "NGO-0000",
    ) -> DueDiligenceReport:
        """Orchestrate statutory due diligence risk assessment."""
        return self.due_diligence_evaluator.evaluate_ngo(
            ngo_name=ngo_name,
            registration_number=registration_number,
            external_id=external_id,
            document_filenames=document_filenames,
            ngo_public_id=ngo_public_id,
        )
