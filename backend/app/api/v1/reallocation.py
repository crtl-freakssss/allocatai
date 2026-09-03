from typing import Dict, Any
from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_request_id,
    get_reallocation_service,
    get_reallocation_engine,
)
from app.services import (
    ReallocationService,
    ReallocationEngine,
)
from app.schemas import (
    ApiResponse,
    ResponseMeta,
    ReallocationRequest,
    ReallocationResult,
)

router = APIRouter()


@router.post(
    "/runs",
    response_model=ApiResponse[ReallocationResult],
    status_code=status.HTTP_201_CREATED,
    summary="Trigger mid-cycle capital reallocation",
)
def create_reallocation_run(
    body: ReallocationRequest,
    request_id: str = Depends(get_request_id),
    realloc_service: ReallocationService = Depends(get_reallocation_service),
    engine: ReallocationEngine = Depends(get_reallocation_engine),
) -> ApiResponse[ReallocationResult]:
    """Execute performance-adjusted reallocation of portfolio allocations."""
    result = realloc_service.create_reallocation_run(
        request=body,
        engine=engine,
        request_id=request_id,
    )
    return ApiResponse(
        data=result,
        meta=ResponseMeta(request_id=request_id),
    )


@router.get(
    "/runs/{id}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get reallocation run details",
)
def get_reallocation_run(
    id: str,
    request_id: str = Depends(get_request_id),
    realloc_service: ReallocationService = Depends(get_reallocation_service),
) -> ApiResponse[Dict[str, Any]]:
    """Retrieve details and performance snapshot of a reallocation run."""
    run = realloc_service.get_reallocation_run(id)
    data = {
        "run_id": run.public_id,
        "previous_optimization_id": run.previous_optimization.public_id if run.previous_optimization else None,
        "budget_paise": run.budget_paise,
        "performance_snapshot": run.performance_snapshot,
        "result_snapshot": run.result_snapshot,
        "calculation_versions": run.calculation_versions,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }
    return ApiResponse(
        data=data,
        meta=ResponseMeta(request_id=request_id),
    )
