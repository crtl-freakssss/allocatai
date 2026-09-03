from typing import List, Dict, Optional, Any
from app.schemas.impact_dna import ImpactDNA
from app.schemas.project import Project as SchemaProject
from app.schemas.geography import Geography
from app.schemas.financials import Financials
from app.schemas.beneficiary import BeneficiaryProfile
from app.schemas.enums import ProjectSector
from app.ai.impact_dna import AIImpactDNAGenerator


class RealImpactDNAEngine:
    """Production Impact DNA profiling engine delegating to Person 2's AIImpactDNAGenerator."""

    def __init__(self, generator: Optional[AIImpactDNAGenerator] = None) -> None:
        self.generator = generator or AIImpactDNAGenerator()

    def generate(
        self,
        project_id: str,
        name: str,
        sector: str,
        requested_amount_paise: int,
        geographies: List[Dict[str, Any]],
        beneficiary_profile: Optional[Dict[str, Any]] = None,
    ) -> ImpactDNA:
        """Generate structured multidimensional Impact DNA characteristics."""

        sector_enum = ProjectSector.EDUCATION
        try:
            sector_enum = ProjectSector(sector.upper())
        except Exception:
            pass

        geos = []
        for g in geographies:
            geos.append(
                Geography(
                    state=g.get("state", "Maharashtra"),
                    district=g.get("district", "Central"),
                    block=g.get("block", "Block-A"),
                )
            )
        if not geos:
            geos = [Geography(state="Maharashtra", district="Central", block="Block-A")]

        b_profile = beneficiary_profile or {}
        reach = b_profile.get("target_count") or max(1000, requested_amount_paise // 50_000)

        dummy_project = SchemaProject(
            project_id=project_id,
            name=name,
            ngo_id="NGO-TEMP",
            sector=sector_enum,
            geographies=geos,
            financials=Financials(requested_amount_paise=requested_amount_paise),
            beneficiary_profile=BeneficiaryProfile(target_count=reach),
            duration_months=12,
            description=f"Intervention {name} in {geos[0].state}.",
            impact_metrics=[],
        )

        impact_dna = self.generator.generate_impact_dna(
            project=dummy_project,
            project_public_id=project_id,
        )
        impact_dna.project_id = project_id
        return impact_dna
