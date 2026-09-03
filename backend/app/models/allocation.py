import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, BigInteger, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.optimization_run import OptimizationRun
    from app.models.project import Project


class Allocation(Base):
    """Project-level allocation decision within an optimization run."""

    __tablename__ = "allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    optimization_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimization_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # ondelete="RESTRICT" enforces Rule 9: Projects in optimization runs must not be hard-deleted
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Monetary allocation stored in paise (BIGINT)
    allocated_amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    # Score fields using exact NUMERIC(6, 5) per contract
    marginal_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    base_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    saturation_index: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    reason_codes: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    rank: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    optimization_run: Mapped["OptimizationRun"] = relationship(
        "OptimizationRun",
        back_populates="allocations",
    )
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="allocations",
    )
