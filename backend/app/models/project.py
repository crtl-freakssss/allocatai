import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, BigInteger, Text, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.proposal import Proposal
    from app.models.ngo import NGO
    from app.models.project_geography import ProjectGeography
    from app.models.impact_dna import ImpactDNA
    from app.models.saturation_result import SaturationResult
    from app.models.allocation import Allocation


class Project(Base):
    """Project entity representing a distinct CSR intervention."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    public_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
    )
    proposal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("proposals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ngo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ngos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sector: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    duration_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    # Monetary values stored in paise (BIGINT)
    requested_amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    current_funding: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    schema_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    proposal: Mapped[Optional["Proposal"]] = relationship(
        "Proposal",
        back_populates="projects",
    )
    ngo: Mapped["NGO"] = relationship(
        "NGO",
        back_populates="projects",
    )
    geographies: Mapped[List["ProjectGeography"]] = relationship(
        "ProjectGeography",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    impact_dna: Mapped[Optional["ImpactDNA"]] = relationship(
        "ImpactDNA",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )
    saturation_results: Mapped[List["SaturationResult"]] = relationship(
        "SaturationResult",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    allocations: Mapped[List["Allocation"]] = relationship(
        "Allocation",
        back_populates="project",
    )
