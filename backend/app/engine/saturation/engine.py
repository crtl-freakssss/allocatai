from typing import Optional
from app.schemas.enums import ProjectSector
from app.schemas.saturation import SaturationResult
from app.engine.saturation.models import STATE_CSR_BENCHMARK_PAISE, DEFAULT_BENCHMARK_PAISE


class RealSaturationEngine:
    """Deterministic regional saturation engine assessing CSR funding density vs need."""

    VERSION: str = "sat-v1"

    def calculate(
        self,
        project_id: str,
        state: str,
        sector: str,
        need_score: float,
        existing_csr_amount_override: Optional[int] = None,
    ) -> SaturationResult:
        """Compute explainable saturation index where low saturation = underserved high need."""
        benchmark_paise = STATE_CSR_BENCHMARK_PAISE.get(state, DEFAULT_BENCHMARK_PAISE)

        # Baseline empirical estimate of existing CSR in this state/sector (or override)
        if existing_csr_amount_override is not None:
            existing_csr_paise = existing_csr_amount_override
        else:
            # Synthetic ratio based on regional benchmark
            existing_csr_paise = int(benchmark_paise * 0.4)

        # Ratio of existing CSR funding to regional benchmark capacity
        funding_ratio = min(2.0, existing_csr_paise / max(1, benchmark_paise))

        # Saturation index: combines funding density (60%) and inverse of need (40%)
        raw_index = (funding_ratio * 0.5) + ((1.0 - need_score) * 0.5)
        saturation_index = max(0.01, min(0.99, round(raw_index, 5)))

        # Estimated coverage is proportional to saturation
        coverage = max(0.05, min(0.95, round(saturation_index * 0.9, 5)))

        # Sector conversion
        try:
            sec_enum = ProjectSector(sector)
        except ValueError:
            sec_enum = ProjectSector.OTHER

        return SaturationResult(
            project_id=project_id,
            state=state,
            sector=sec_enum,
            saturation_index=saturation_index,
            need_score=round(need_score, 5),
            existing_csr_amount_paise=existing_csr_paise,
            estimated_beneficiary_coverage=coverage,
            confidence=0.88,
            calculation_version=self.VERSION,
        )
