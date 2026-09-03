from typing import Generator, Tuple, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import get_settings

settings = get_settings()

# Configure SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> Tuple[bool, Optional[str]]:
    """Check database connectivity without leaking sensitive credentials.

    Returns:
        (True, None) if connection succeeds.
        (False, sanitized_error_message) if connection fails.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, None
    except Exception as exc:
        # Sanitize message so database password or internal URLs are not exposed
        exc_type = type(exc).__name__
        return False, f"Database connectivity check failed ({exc_type})"


def close_db_connection() -> None:
    """Dispose engine connections on application shutdown."""
    engine.dispose()
