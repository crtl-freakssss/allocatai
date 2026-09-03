import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.proposal import Proposal
    from app.models.project import Project
    from app.models.due_diligence_report import DueDiligenceReport


class NGO(Base):
    """Non-Governmental Organization (NGO) entity implementing social impact projects."""

    __tablename__ = "ngos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    registration_number: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
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
    proposals: Mapped[List["Proposal"]] = relationship(
        "Proposal",
        back_populates="ngo",
        cascade="all, delete-orphan",
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="ngo",
        cascade="all, delete-orphan",
    )
    due_diligence_reports: Mapped[List["DueDiligenceReport"]] = relationship(
        "DueDiligenceReport",
        back_populates="ngo",
        cascade="all, delete-orphan",
    )
