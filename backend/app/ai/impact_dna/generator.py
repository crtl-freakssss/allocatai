import logging
from typing import Optional, Dict, Any

from app.ai.client import LLMClient
from app.ai.schemas.impact_dna import AIImpactDNADTO
from app.ai.prompts.impact_dna import IMPACT_DNA_SYSTEM_PROMPT, IMPACT_DNA_USER_PROMPT_TEMPLATE
from app.schemas.project import Project as SchemaProject
from app.schemas.impact_dna import ImpactDNA as SchemaImpactDNA

logger = logging.getLogger(__name__)


class AIImpactDNAGenerator:
    """AI engine computing multi-dimensional Impact DNA metrics mapped to canonical backend schemas."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def generate_impact_dna(
        self,
        project: SchemaProject,
        project_public_id: str = "PRJ-0000",
    ) -> SchemaImpactDNA:
        """Generate canonical ImpactDNA schema from Project input."""

        state = project.geographies[0].state if project.geographies else "Maharashtra"
        district = project.geographies[0].district if project.geographies else "Central"
        req_paise = project.financials.requested_amount_paise if project.financials else 500_000_000

        user_prompt = IMPACT_DNA_USER_PROMPT_TEMPLATE.format(
            name=project.name,
            sector=project.sector.value,
            state=state,
            district=district,
            requested_amount_paise=req_paise,
            beneficiary_count=project.beneficiary_profile.target_count,
            description=project.description or "",
        )

        fallback_dict = self._build_fallback_data(project, state, req_paise)

        ai_output: AIImpactDNADTO = self.llm_client.generate_structured_output(
            system_prompt=IMPACT_DNA_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=AIImpactDNADTO,
            fallback_data=fallback_dict,
        )

        model_tag = self.llm_client.model if self.llm_client.is_live else "impact-dna-v1"
        prompt_tag = "impact-dna-v2.0" if self.llm_client.is_live else "dna-v1.0"

        return SchemaImpactDNA(
            dna_id="DNA-TEMP",
            project_id=project_public_id,
            need_score=round(ai_output.need_score, 5),
            expected_impact_score=round(ai_output.expected_impact_score, 5),
            cost_efficiency_score=round(ai_output.cost_efficiency_score, 5),
            evidence_strength_score=round(ai_output.evidence_strength_score, 5),
            scalability_score=round(ai_output.scalability_score, 5),
            implementation_risk_score=round(ai_output.implementation_risk_score, 5),
            beneficiary_reach=ai_output.beneficiary_reach,
            estimated_impact_per_lakh=round(ai_output.estimated_impact_per_lakh, 4),
            missing_fields=ai_output.missing_fields,
            extraction_confidence=round(ai_output.extraction_confidence, 5),
            model_name=model_tag,
            prompt_version=prompt_tag,
        )

    def _build_fallback_data(
        self, project: SchemaProject, state: str, req_paise: int
    ) -> Dict[str, Any]:
        """Construct fallback Impact DNA data based on regional need heuristics."""
        high_need_states = {"Bihar", "Assam", "Jharkhand", "Uttar Pradesh", "Odisha", "Chhattisgarh"}
        need_score = 0.92 if state in high_need_states else 0.72
        expected_impact = min(0.98, need_score * 0.95 + 0.05)
        reach = project.beneficiary_profile.target_count or max(1000, req_paise // 50_000)

        return {
            "need_score": need_score,
            "expected_impact_score": expected_impact,
            "cost_efficiency_score": 0.82,
            "evidence_strength_score": 0.85,
            "scalability_score": 0.80,
            "implementation_risk_score": 0.15,
            "beneficiary_reach": reach,
            "estimated_impact_per_lakh": round(need_score * 45.0, 2),
            "missing_fields": [],
            "extraction_confidence": 0.95,
        }
