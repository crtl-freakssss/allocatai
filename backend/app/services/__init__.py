"""Service / Orchestration Layer for AllocateAI platform.

Orchestrates multi-entity business workflows, owns transaction boundaries,
coordinates repositories and mathematical/AI engines, and logs tamper-evident audit events.
"""

from app.services.exceptions import (
    AllocateAIServiceError,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    ServiceValidationError,
    ConflictError,
    InvalidStateTransitionError,
    ProcessingError,
)
from app.services.interfaces import (
    ExtractionEngine,
    ImpactDNAEngine,
    SaturationEngine,
    OptimizationEngine,
    ReallocationEngine,
    DueDiligenceEngine,
)
from app.services.audit import AuditService
from app.services.proposal import ProposalService
from app.services.document import DocumentService
from app.services.extraction import ExtractionService
from app.services.project import ProjectService
from app.services.impact_dna import ImpactDNAService
from app.services.saturation import SaturationService
from app.services.optimization import OptimizationService
from app.services.reallocation import ReallocationService
from app.services.due_diligence import DueDiligenceService

__all__ = [
    # Exceptions
    "AllocateAIServiceError",
    "ResourceNotFoundError",
    "ResourceAlreadyExistsError",
    "ServiceValidationError",
    "ConflictError",
    "InvalidStateTransitionError",
    "ProcessingError",
    # Interfaces
    "ExtractionEngine",
    "ImpactDNAEngine",
    "SaturationEngine",
    "OptimizationEngine",
    "ReallocationEngine",
    "DueDiligenceEngine",
    # Services
    "AuditService",
    "ProposalService",
    "DocumentService",
    "ExtractionService",
    "ProjectService",
    "ImpactDNAService",
    "SaturationService",
    "OptimizationService",
    "ReallocationService",
    "DueDiligenceService",
]
