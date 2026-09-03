import pytest
from unittest.mock import patch
from fastapi import status
from fastapi.testclient import TestClient
from app.main import app


def test_app_imports():
    """Verify that the FastAPI application can be imported cleanly."""
    assert app is not None
    assert app.title == "AllocateAI Backend"


def test_health_liveness_endpoint(client):
    """Verify GET /api/v1/health returns 200 with standard success envelope."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK

    body = response.json()
    assert "data" in body, "Response must contain 'data' key"
    assert "meta" in body, "Response must contain 'meta' key"

    # Verify data content
    data = body["data"]
    assert data["status"] == "healthy"
    assert data["service"] == "AllocateAI Backend"
    assert "version" in data
    assert "environment" in data

    # Verify meta content
    meta = body["meta"]
    assert "request_id" in meta
    assert meta["request_id"].startswith("req_")
    assert meta["schema_version"] == "v1"
    assert "timestamp" in meta

    # Verify X-Request-ID header
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == meta["request_id"]


def test_request_id_preservation(client):
    """Verify that a client-provided X-Request-ID header is preserved."""
    custom_id = "test-custom-request-id-9988"
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == status.HTTP_200_OK

    body = response.json()
    assert body["meta"]["request_id"] == custom_id
    assert response.headers.get("X-Request-ID") == custom_id


def test_readiness_endpoint_real_call(client):
    """Verify GET /api/v1/health/ready returns either 200 or 503 based on actual DB state."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]

    body = response.json()
    if response.status_code == status.HTTP_200_OK:
        assert "data" in body
        assert body["data"]["status"] == "ready"
        assert body["data"]["database"] == "connected"
        assert "meta" in body
        assert "request_id" in body["meta"]
    else:
        assert "error" in body
        assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert body["error"]["details"]["database"] == "disconnected"
        assert "request_id" in body["error"]


def test_readiness_when_db_connected(client):
    """Verify GET /api/v1/health/ready contract when database connection succeeds."""
    with patch("app.api.v1.health.check_db_connection", return_value=(True, None)):
        response = client.get("/api/v1/health/ready")
        assert response.status_code == status.HTTP_200_OK

        body = response.json()
        assert "data" in body
        assert body["data"]["status"] == "ready"
        assert body["data"]["database"] == "connected"
        assert "meta" in body
        assert "request_id" in body["meta"]
        assert "X-Request-ID" in response.headers


def test_readiness_when_db_disconnected(client):
    """Verify GET /api/v1/health/ready contract when database connection fails."""
    with patch(
        "app.api.v1.health.check_db_connection",
        return_value=(False, "Database connectivity check failed (OperationalError)"),
    ):
        response = client.get("/api/v1/health/ready")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        body = response.json()
        assert "error" in body
        assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert "Database is not ready" in body["error"]["message"]
        assert body["error"]["details"]["database"] == "disconnected"
        assert "request_id" in body["error"]
        assert "X-Request-ID" in response.headers


def test_404_error_envelope(client):
    """Verify 404 routes return the standard error envelope."""
    response = client.get("/api/v1/nonexistent-endpoint")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    body = response.json()
    assert "error" in body
    error = body["error"]
    assert error["code"] == "RESOURCE_NOT_FOUND"
    assert "message" in error
    assert "request_id" in error
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == error["request_id"]


def test_internal_server_error_envelope():
    """Verify unhandled exceptions return 500 error envelope and hide stack traces."""
    safe_client = TestClient(app, raise_server_exceptions=False)
    with patch("app.api.v1.health.build_envelope", side_effect=RuntimeError("Secret database error")):
        response = safe_client.get("/api/v1/health")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        body = response.json()
        assert "error" in body
        error = body["error"]
        assert error["code"] == "INTERNAL_SERVER_ERROR"
        assert "Secret database error" not in error["message"], "Internal errors must not leak details"
        assert error["message"] == "An unexpected internal server error occurred."
        assert "request_id" in error
        assert "X-Request-ID" in response.headers
