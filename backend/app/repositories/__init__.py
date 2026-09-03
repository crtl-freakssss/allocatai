"""Repository / Data Access Layer for AllocateAI platform.

Repositories handle database reads, inserts, updates, and constraint-aware persistence
cooperating with SQLAlchemy transaction management.
"""

from app.repositories.base import BaseRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository
from app.repositories.ngo import NGORepository
from app.repositories.proposal import ProposalRepository
from app.repositories.document import DocumentRepository
from app.repositories.project import ProjectRepository
from app.repositories.impact_dna import ImpactDNARepository
from app.repositories.saturation import SaturationRepository
from app.repositories.due_diligence import DueDiligenceRepository
from app.repositories.optimization import OptimizationRepository
from app.repositories.allocation import AllocationRepository
from app.repositories.reallocation import ReallocationRepository
from app.repositories.audit import AuditRepository

__all__ = [
    "BaseRepository",
    "OrganizationRepository",
    "UserRepository",
    "NGORepository",
    "ProposalRepository",
    "DocumentRepository",
    "ProjectRepository",
    "ImpactDNARepository",
    "SaturationRepository",
    "DueDiligenceRepository",
    "OptimizationRepository",
    "AllocationRepository",
    "ReallocationRepository",
    "AuditRepository",
]
