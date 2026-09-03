import pytest
from app.config.settings import Settings, get_settings
from app.db.base import Base
from app.db.session import SessionLocal, get_db


def test_settings_defaults():
    """Verify default configuration settings."""
    settings = get_settings()
    assert settings.app_name == "AllocateAI Backend"
    assert settings.api_v1_prefix == "/api/v1"
    assert isinstance(settings.cors_origin_list, list)
    assert len(settings.cors_origin_list) > 0


def test_cors_origins_parsing():
    """Verify comma-separated string parsing for CORS origins."""
    s1 = Settings(cors_origins="http://localhost:3000,http://example.com")
    assert s1.cors_origin_list == ["http://localhost:3000", "http://example.com"]

    s2 = Settings(cors_origins=["http://localhost:3000"])
    assert s2.cors_origin_list == ["http://localhost:3000"]


def test_declarative_base():
    """Verify SQLAlchemy Base exists and has metadata."""
    assert hasattr(Base, "metadata")


def test_get_db_generator():
    """Verify get_db returns a generator yielding a Session."""
    db_gen = get_db()
    session = next(db_gen)
    assert session is not None
    # Close generator cleanly
    try:
        next(db_gen)
    except StopIteration:
        pass
