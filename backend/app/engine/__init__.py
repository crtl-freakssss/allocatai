"""AllocateAI Intelligence Engines.

Houses concrete mathematical solvers, machine learning pipelines, and extraction services
implementing the Phase 4 engine Protocol interfaces.
"""

from app.engine.extraction import RealExtractionEngine, DocumentParser, StructuredExtractionClient
from app.engine.impact_dna import RealImpactDNAEngine
from app.engine.scoring import ScoringEngine
from app.engine.saturation import RealSaturationEngine
from app.engine.marginal_impact import MarginalImpactCalculator
from app.engine.optimizer import RealOptimizationEngine, MILPOptimizerFormulation
from app.engine.reallocation import RealReallocationEngine
from app.engine.due_diligence import RealDueDiligenceEngine

__all__ = [
    "RealExtractionEngine",
    "DocumentParser",
    "StructuredExtractionClient",
    "RealImpactDNAEngine",
    "ScoringEngine",
    "RealSaturationEngine",
    "MarginalImpactCalculator",
    "RealOptimizationEngine",
    "MILPOptimizerFormulation",
    "RealReallocationEngine",
    "RealDueDiligenceEngine",
]
