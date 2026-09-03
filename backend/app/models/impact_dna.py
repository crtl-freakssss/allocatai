import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import String, BigInteger, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class ImpactDNA(Base):
    """Impact DNA metrics extracted and computed for a project."""

    __tablename__ = "impact_dna"

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
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Score fields using exact NUMERIC(6, 5) per contract
    need_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    expected_impact_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    cost_efficiency_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    evidence_strength_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    scalability_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    implementation_risk_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    beneficiary_reach: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )
    estimated_impact_per_lakh: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=14, scale=4),
        nullable=True,
    )
    missing_fields: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    extraction_confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    model_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    prompt_version: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    schema_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="impact_dna",
    )
