import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    """TestClient fixture for making API requests."""
    with TestClient(app) as test_client:
        yield test_client
