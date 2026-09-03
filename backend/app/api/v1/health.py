from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from app.config.settings import get_settings
from app.db.session import check_db_connection
from app.schemas.common import build_envelope, build_error_envelope

router = APIRouter()
settings = get_settings()


@router.get(
    "",
    summary="Application Health Check",
    description="Liveness probe indicating the backend service is running. Does not depend on the database.",
)
async def get_health(request: Request):
    """Liveness probe returning 200 OK if service is up."""
    request_id = getattr(request.state, "request_id", "unknown")
    payload = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=build_envelope(
            data=payload,
            request_id=request_id,
            schema_version=settings.schema_version,
        ),
    )


@router.get(
    "/ready",
    summary="Application Readiness Probe",
    description="Readiness probe verifying service readiness and PostgreSQL database connectivity.",
)
async def get_readiness(request: Request):
    """Readiness probe checking database connectivity."""
    request_id = getattr(request.state, "request_id", "unknown")
    is_connected, error_msg = check_db_connection()

    if is_connected:
        payload = {
            "status": "ready",
            "service": settings.app_name,
            "database": "connected",
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=build_envelope(
                data=payload,
                request_id=request_id,
                schema_version=settings.schema_version,
            ),
        )

    # If database is unavailable, return 503 Service Unavailable
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=build_error_envelope(
            code="SERVICE_UNAVAILABLE",
            message="Database is not ready or connection failed.",
            request_id=request_id,
            details={
                "status": "not_ready",
                "database": "disconnected",
                "reason": error_msg or "Connection refused",
            },
        ),
    )
