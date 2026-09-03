import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.config.settings import get_settings

settings = get_settings()


@pytest.fixture(scope="module")
def repo_engine():
    """Create test engine connected to the PostgreSQL database."""
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def repo_session(repo_engine):
    """Provide a clean transactional database session that rolls back after each test."""
    connection = repo_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()
