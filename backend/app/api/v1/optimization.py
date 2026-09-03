from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    get_request_id,
    get_optimization_service,
    get_optimization_engine,
)
from app.services import (
    OptimizationService,
    OptimizationEngine,
)
from app.schemas import (
    ApiResponse,
    ApiCollectionResponse,
    ResponseMeta,
    PaginationMeta,
    OptimizationRequest,
    OptimizationResult,
)

router = APIRouter()


@router.post(
    "/runs",
    response_model=ApiResponse[OptimizationResult],
    status_code=status.HTTP_201_CREATED,
    summary="Create and execute an optimization run",
)
def create_optimization_run(
    body: OptimizationRequest,
    request_id: str = Depends(get_request_id),
    opt_service: OptimizationService = Depends(get_optimization_service),
    engine: OptimizationEngine = Depends(get_optimization_engine),
) -> ApiResponse[OptimizationResult]:
    """Execute MILP portfolio optimization, validate invariants, and persist allocations atomically."""
    result = opt_service.create_optimization_run(
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
    summary="Get optimization run details",
)
def get_optimization_run(
    id: str,
    request_id: str = Depends(get_request_id),
    opt_service: OptimizationService = Depends(get_optimization_service),
) -> ApiResponse[Dict[str, Any]]:
    """Retrieve details, input snapshot, and immutable result snapshot of an optimization run."""
    run = opt_service.get_optimization_run(id)
    allocations_data = [
        {
            "project_id": a.project.public_id,
            "allocated_amount_paise": a.allocated_amount,
            "marginal_score": float(a.marginal_score) if a.marginal_score else 0.0,
            "base_score": float(a.base_score) if a.base_score else 0.0,
            "saturation_index": float(a.saturation_index) if a.saturation_index else 0.0,
            "rank": a.rank,
            "status": a.status,
            "reason_codes": a.reason_codes.get("codes", []),
        }
        for a in run.allocations
    ]
    data = {
        "run_id": run.public_id,
        "status": run.status,
        "budget_paise": run.budget_paise,
        "total_predicted_impact": float(run.total_predicted_impact) if run.total_predicted_impact else 0.0,
        "input_snapshot": run.input_snapshot,
        "result_snapshot": run.result_snapshot,
        "allocations": allocations_data,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": getattr(run, "updated_at", None).isoformat() if getattr(run, "updated_at", None) else None,
    }
    return ApiResponse(
        data=data,
        meta=ResponseMeta(request_id=request_id),
    )


@router.get(
    "/runs",
    response_model=ApiCollectionResponse[Dict[str, Any]],
    summary="List optimization runs",
)
def list_optimization_runs(
    status: Optional[str] = Query(None, description="Filter by status (e.g. COMPLETED, RUNNING, FAILED)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    request_id: str = Depends(get_request_id),
    opt_service: OptimizationService = Depends(get_optimization_service),
) -> ApiCollectionResponse[Dict[str, Any]]:
    """List historical optimization solver runs with pagination."""
    items, total = opt_service.list_optimization_runs(status=status, page=page, page_size=page_size)
    responses = [
        {
            "run_id": r.public_id,
            "status": r.status,
            "budget_paise": r.budget_paise,
            "total_predicted_impact": float(r.total_predicted_impact) if r.total_predicted_impact else 0.0,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in items
    ]
    return ApiCollectionResponse(
        data=responses,
        meta=ResponseMeta(
            request_id=request_id,
            pagination=PaginationMeta(page=page, page_size=page_size, total=total),
        ),
    )
