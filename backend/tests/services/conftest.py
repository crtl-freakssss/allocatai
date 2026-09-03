import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.config.settings import get_settings

settings = get_settings()


@pytest.fixture(scope="module")
def service_engine():
    """Module-level engine connected to test PostgreSQL database."""
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def service_session(service_engine):
    """Function-level transactional session that rolls back after each test."""
    connection = service_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()
