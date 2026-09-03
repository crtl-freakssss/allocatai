import uuid
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.saturation_result import SaturationResult
from app.repositories.base import BaseRepository


class SaturationRepository(BaseRepository[SaturationResult]):
    """Data access repository for SaturationResult analytics records."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, SaturationResult)

    def create(
        self,
        project_id: uuid.UUID,
        state: str,
        sector: str,
        saturation_index: Decimal,
        need_score: Decimal,
        existing_csr_amount: int,
        beneficiary_coverage: Decimal,
        confidence: Decimal,
        calculation_version: str = "saturation-v1",
    ) -> SaturationResult:
        """Create and persist a saturation assessment entry."""
        sat = SaturationResult(
            project_id=project_id,
            state=state,
            sector=sector,
            saturation_index=saturation_index,
            need_score=need_score,
            existing_csr_amount=existing_csr_amount,
            beneficiary_coverage=beneficiary_coverage,
            confidence=confidence,
            calculation_version=calculation_version,
        )
        return self.add(sat, flush=True)

    def get_by_project_id(self, project_id: uuid.UUID) -> List[SaturationResult]:
        """Fetch all saturation records calculated for a project."""
        stmt = (
            select(SaturationResult)
            .where(SaturationResult.project_id == project_id)
            .order_by(SaturationResult.created_at.desc(), SaturationResult.id.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_latest_for_project(self, project_id: uuid.UUID) -> Optional[SaturationResult]:
        """Fetch the latest saturation record for a project."""
        stmt = (
            select(SaturationResult)
            .where(SaturationResult.project_id == project_id)
            .order_by(SaturationResult.created_at.desc(), SaturationResult.id.asc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def list_by_state(self, state: str) -> List[SaturationResult]:
        """List saturation records matching a given state."""
        stmt = (
            select(SaturationResult)
            .where(SaturationResult.state == state)
            .order_by(SaturationResult.created_at.desc(), SaturationResult.id.asc())
        )
        return list(self.session.scalars(stmt).all())

    def list_by_sector(self, sector: str) -> List[SaturationResult]:
        """List saturation records matching a given sector."""
        stmt = (
            select(SaturationResult)
            .where(SaturationResult.sector == sector)
            .order_by(SaturationResult.created_at.desc(), SaturationResult.id.asc())
        )
        return list(self.session.scalars(stmt).all())
