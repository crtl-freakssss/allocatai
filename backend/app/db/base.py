from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class for AllocateAI database models."""

    pass


# Import all models to register them on Base.metadata for Alembic discovery
import app.models  # noqa: F401, E402
