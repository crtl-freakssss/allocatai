import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import String, BigInteger, Numeric, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.allocation import Allocation
    from app.models.reallocation_run import ReallocationRun


class OptimizationRun(Base):
    """Portfolio optimization execution containing immutable input and result snapshots."""

    __tablename__ = "optimization_runs"

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
    # Total portfolio optimization budget stored in paise (BIGINT)
    budget_paise: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    weights: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    constraints: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    calculation_versions: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    # Immutable audit snapshots of inputs and solver results
    input_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    result_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    total_predicted_impact: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=True,
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
    allocations: Mapped[List["Allocation"]] = relationship(
        "Allocation",
        back_populates="optimization_run",
        cascade="all, delete-orphan",
    )
    reallocation_runs: Mapped[List["ReallocationRun"]] = relationship(
        "ReallocationRun",
        back_populates="previous_optimization",
    )
