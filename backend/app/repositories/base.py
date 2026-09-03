from typing import Generic, TypeVar, Type, Optional, Any
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select, func

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository providing fundamental SQLAlchemy session interaction.

    Transaction ownership remains with the caller/service layer.
    Repositories only flush/refresh when required for primary key or default generation.
    """

    def __init__(self, session: Session, model_cls: Type[T]) -> None:
        self.session = session
        self.model_cls = model_cls

    def get_by_id(self, entity_id: uuid.UUID) -> Optional[T]:
        """Fetch a single record by primary key UUID."""
        return self.session.get(self.model_cls, entity_id)

    def add(self, entity: T, flush: bool = True) -> T:
        """Add an entity to session and optionally flush to obtain database defaults."""
        self.session.add(entity)
        if flush:
            self.session.flush()
        return entity

    def refresh(self, entity: T) -> T:
        """Refresh instance state from database within current transaction."""
        self.session.refresh(entity)
        return entity

    def delete(self, entity: T, flush: bool = True) -> None:
        """Mark an entity for deletion within current transaction."""
        self.session.delete(entity)
        if flush:
            self.session.flush()

    def exists(self, entity_id: uuid.UUID) -> bool:
        """Check whether a record with the given primary key exists."""
        stmt = select(func.count()).select_from(self.model_cls).where(self.model_cls.id == entity_id)
        count = self.session.scalar(stmt) or 0
        return count > 0
