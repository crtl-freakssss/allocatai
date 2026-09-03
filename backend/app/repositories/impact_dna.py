import uuid
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.impact_dna import ImpactDNA
from app.repositories.base import BaseRepository


class ImpactDNARepository(BaseRepository[ImpactDNA]):
    """Data access repository for ImpactDNA 1-to-1 project dimension profiles."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, ImpactDNA)

    def create(
        self,
        public_id: str,
        project_id: uuid.UUID,
        need_score: Decimal,
        expected_impact_score: Decimal,
        cost_efficiency_score: Decimal,
        evidence_strength_score: Decimal,
        scalability_score: Decimal,
        implementation_risk_score: Decimal,
        beneficiary_reach: int,
        estimated_impact_per_lakh: Decimal,
        missing_fields: Dict[str, Any],
        extraction_confidence: Decimal,
        model_name: str,
        prompt_version: str,
        schema_version: str = "v1",
    ) -> ImpactDNA:
        """Create and persist an Impact DNA score profile."""
        dna = ImpactDNA(
            public_id=public_id,
            project_id=project_id,
            need_score=need_score,
            expected_impact_score=expected_impact_score,
            cost_efficiency_score=cost_efficiency_score,
            evidence_strength_score=evidence_strength_score,
            scalability_score=scalability_score,
            implementation_risk_score=implementation_risk_score,
            beneficiary_reach=beneficiary_reach,
            estimated_impact_per_lakh=estimated_impact_per_lakh,
            missing_fields=missing_fields,
            extraction_confidence=extraction_confidence,
            model_name=model_name,
            prompt_version=prompt_version,
            schema_version=schema_version,
        )
        return self.add(dna, flush=True)

    def get_by_public_id(self, public_id: str) -> Optional[ImpactDNA]:
        """Fetch ImpactDNA by public identifier (e.g. DNA-0001)."""
        stmt = select(ImpactDNA).where(ImpactDNA.public_id == public_id)
        return self.session.scalar(stmt)

    def get_by_project_id(self, project_id: uuid.UUID) -> Optional[ImpactDNA]:
        """Fetch ImpactDNA for a project (1-to-1 relationship)."""
        stmt = select(ImpactDNA).where(ImpactDNA.project_id == project_id)
        return self.session.scalar(stmt)

    def update(
        self,
        dna: ImpactDNA,
        need_score: Optional[Decimal] = None,
        expected_impact_score: Optional[Decimal] = None,
        cost_efficiency_score: Optional[Decimal] = None,
        evidence_strength_score: Optional[Decimal] = None,
        scalability_score: Optional[Decimal] = None,
        implementation_risk_score: Optional[Decimal] = None,
        beneficiary_reach: Optional[int] = None,
        estimated_impact_per_lakh: Optional[Decimal] = None,
        extraction_confidence: Optional[Decimal] = None,
    ) -> ImpactDNA:
        """Update scores or reach metrics on an existing ImpactDNA record."""
        if need_score is not None:
            dna.need_score = need_score
        if expected_impact_score is not None:
            dna.expected_impact_score = expected_impact_score
        if cost_efficiency_score is not None:
            dna.cost_efficiency_score = cost_efficiency_score
        if evidence_strength_score is not None:
            dna.evidence_strength_score = evidence_strength_score
        if scalability_score is not None:
            dna.scalability_score = scalability_score
        if implementation_risk_score is not None:
            dna.implementation_risk_score = implementation_risk_score
        if beneficiary_reach is not None:
            dna.beneficiary_reach = beneficiary_reach
        if estimated_impact_per_lakh is not None:
            dna.estimated_impact_per_lakh = estimated_impact_per_lakh
        if extraction_confidence is not None:
            dna.extraction_confidence = extraction_confidence
        self.session.flush()
        return dna
