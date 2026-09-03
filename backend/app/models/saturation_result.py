import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, BigInteger, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class SaturationResult(Base):
    """Regional saturation analytics for a project's state and sector."""

    __tablename__ = "saturation_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    sector: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    saturation_index: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    need_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    # Existing CSR funding in the region stored in paise (BIGINT)
    existing_csr_amount: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )
    beneficiary_coverage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=5),
        nullable=True,
    )
    calculation_version: Mapped[Optional[str]] = mapped_column(
        String(100),
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
        back_populates="saturation_results",
    )
