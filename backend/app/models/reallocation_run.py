import uuid
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.optimization_run import OptimizationRun


class ReallocationRun(Base):
    """Reallocation run executing mid-cycle portfolio rebalancing without overwriting previous runs."""

    __tablename__ = "reallocation_runs"

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
    # Foreign key referencing prior optimization run without mutating it
    previous_optimization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimization_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Reallocation budget stored in paise (BIGINT)
    budget_paise: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    performance_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    result_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    calculation_versions: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    previous_optimization: Mapped["OptimizationRun"] = relationship(
        "OptimizationRun",
        back_populates="reallocation_runs",
    )
