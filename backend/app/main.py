import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.config.settings import get_settings
from app.db.session import close_db_connection
from app.schemas.common import build_error_envelope
from app.services.exceptions import (
    AllocateAIServiceError,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    ServiceValidationError,
    ConflictError,
    InvalidStateTransitionError,
    ProcessingError,
)

# Configure logging compatible with Python 3.10+
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("allocateai")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("Starting AllocateAI Backend")
    logger.info(
        "Environment: %s | Debug: %s | API Prefix: %s",
        settings.environment,
        settings.debug,
        settings.api_v1_prefix,
    )
    try:
        from app.db.seed import seed_demo_data_if_needed
        seed_demo_data_if_needed()
    except Exception as e:
        logger.warning("Seed demo data skipped or failed: %s", e)
    yield
    logger.info("Shutting down AllocateAI Backend...")
    close_db_connection()
    logger.info("AllocateAI Backend shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AllocateAI Platform Backend API",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Middleware ensuring every request has a tracked X-Request-ID."""
    client_request_id = request.headers.get("X-Request-ID")
    if client_request_id and client_request_id.strip():
        request_id = client_request_id.strip()
    else:
        request_id = f"req_{uuid.uuid4().hex[:12]}"

    # Attach to request state for access in endpoints and exception handlers
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# --- Centralized Exception Handlers ---

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Format HTTP exceptions into the standard AllocateAI error envelope."""
    request_id = getattr(request.state, "request_id", "unknown")
    code = f"HTTP_{exc.status_code}"
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "RESOURCE_NOT_FOUND"
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "UNAUTHORIZED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"

    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_envelope(
            code=code,
            message=str(exc.detail),
            request_id=request_id,
            details={},
        ),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format validation errors into the standard AllocateAI error envelope."""
    request_id = getattr(request.state, "request_id", "unknown")
    # Clean validation errors for serializability
    clean_errors = []
    for error in exc.errors():
        clean_errors.append(
            {
                "loc": list(error.get("loc", [])),
                "msg": error.get("msg", ""),
                "type": error.get("type", ""),
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_error_envelope(
            code="VALIDATION_ERROR",
            message="The request failed validation checks.",
            request_id=request_id,
            details={"errors": clean_errors},
        ),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=build_error_envelope(
            code="RESOURCE_NOT_FOUND",
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        ),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(ResourceAlreadyExistsError)
async def resource_already_exists_handler(request: Request, exc: ResourceAlreadyExistsError):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=build_error_envelope(
            code="RESOURCE_ALREADY_EXISTS",
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        ),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=build_error_envelope(
            code="CONFLICT",
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        ),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(ServiceValidationError)
async def service_validation_handler(request: Request, exc: ServiceValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_error_envelope(
            code="VALIDATION_ERROR",
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        ),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(InvalidStateTransitionError)
async def invalid_state_transition_handler(request: Request, exc: InvalidStateTransitionError):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=build_error_envelope(
            code="INVALID_STATE_TRANSITION",
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        ),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(ProcessingError)
async def processing_error_handler(request: Request, exc: ProcessingError):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_error_envelope(
            code="PROCESSING_ERROR",
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        ),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to prevent leaking stack traces or credentials."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error("Unhandled internal exception: %s", exc, exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=build_error_envelope(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
            request_id=request_id,
            details={},
        ),
        headers={"X-Request-ID": request_id},
    )


# Register API v1 Router
app.include_router(api_router, prefix=settings.api_v1_prefix)
