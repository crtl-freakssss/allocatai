from typing import Optional
from app.schemas.due_diligence import DueDiligenceReport
from app.ai.due_diligence import AIDueDiligenceEvaluator


class RealDueDiligenceEngine:
    """Production NGO due diligence evaluation engine delegating to Person 2's AIDueDiligenceEvaluator."""

    def __init__(self, evaluator: Optional[AIDueDiligenceEvaluator] = None) -> None:
        self.evaluator = evaluator or AIDueDiligenceEvaluator()

    def evaluate(
        self,
        ngo_id: str,
        name: str,
        registration_number: Optional[str] = None,
        report_id: Optional[str] = None,
    ) -> DueDiligenceReport:
        """Evaluate statutory registration compliance, risk markers, and generate evidence report."""
        report = self.evaluator.evaluate_ngo(
            ngo_name=name,
            registration_number=registration_number,
            ngo_public_id=ngo_id,
        )
        report.ngo_id = ngo_id
        if report_id:
            report.report_id = report_id
        return report
