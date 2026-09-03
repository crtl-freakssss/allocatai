import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.ngo import NGO


class DueDiligenceReport(Base):
    """Due diligence assessment report generated for an NGO."""

    __tablename__ = "due_diligence_reports"

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
    ngo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ngos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    risk_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    checks: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    flags: Mapped[Optional[List[Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    missing_documents: Mapped[Optional[List[Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    model_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    model_version: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    ngo: Mapped["NGO"] = relationship(
        "NGO",
        back_populates="due_diligence_reports",
    )
