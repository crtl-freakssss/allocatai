from typing import Optional
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import (
    ProposalService,
    DocumentService,
    ExtractionService,
    ProjectService,
    ImpactDNAService,
    OptimizationService,
    ReallocationService,
    DueDiligenceService,
    AuditService,
    ExtractionEngine,
    ImpactDNAEngine,
    OptimizationEngine,
    ReallocationEngine,
    DueDiligenceEngine,
)
from tests.services.fake_engines import (
    FakeExtractionEngine,
    FakeOptimizationEngine,
    FakeReallocationEngine,
    FakeDueDiligenceEngine,
)


def get_request_id(request: Request) -> str:
    """Retrieve tracked X-Request-ID from request state."""
    return getattr(request.state, "request_id", "req_unknown")


def get_proposal_service(session: Session = Depends(get_db)) -> ProposalService:
    """Dependency providing ProposalService instance."""
    return ProposalService(session=session)


def get_document_service(session: Session = Depends(get_db)) -> DocumentService:
    """Dependency providing DocumentService instance."""
    return DocumentService(session=session)


def get_extraction_service(session: Session = Depends(get_db)) -> ExtractionService:
    """Dependency providing ExtractionService instance."""
    return ExtractionService(session=session)


def get_project_service(session: Session = Depends(get_db)) -> ProjectService:
    """Dependency providing ProjectService instance."""
    return ProjectService(session=session)


def get_impact_dna_service(session: Session = Depends(get_db)) -> ImpactDNAService:
    """Dependency providing ImpactDNAService instance."""
    return ImpactDNAService(session=session)


def get_optimization_service(session: Session = Depends(get_db)) -> OptimizationService:
    """Dependency providing OptimizationService instance."""
    return OptimizationService(session=session)


def get_reallocation_service(session: Session = Depends(get_db)) -> ReallocationService:
    """Dependency providing ReallocationService instance."""
    return ReallocationService(session=session)


def get_due_diligence_service(session: Session = Depends(get_db)) -> DueDiligenceService:
    """Dependency providing DueDiligenceService instance."""
    return DueDiligenceService(session=session)


def get_audit_service(session: Session = Depends(get_db)) -> AuditService:
    """Dependency providing AuditService instance."""
    return AuditService(session=session)


from app.engine import (
    RealExtractionEngine,
    RealImpactDNAEngine,
    RealOptimizationEngine,
    RealReallocationEngine,
    RealDueDiligenceEngine,
)


# --- Default Engine Providers (Can be overridden via app.dependency_overrides) ---

def get_extraction_engine() -> ExtractionEngine:
    """Default production extraction engine provider."""
    return RealExtractionEngine()


def get_impact_dna_engine() -> ImpactDNAEngine:
    """Default production Impact DNA profiling engine provider."""
    return RealImpactDNAEngine()


def get_optimization_engine() -> OptimizationEngine:
    """Default production portfolio optimization solver provider."""
    return RealOptimizationEngine()


def get_reallocation_engine() -> ReallocationEngine:
    """Default production mid-cycle capital reallocation solver provider."""
    return RealReallocationEngine()


def get_due_diligence_engine() -> DueDiligenceEngine:
    """Default production due diligence verification engine provider."""
    return RealDueDiligenceEngine()
