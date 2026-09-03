import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    get_request_id,
    get_project_service,
    get_impact_dna_service,
    get_impact_dna_engine,
)
from app.services import ProjectService, ImpactDNAService, ImpactDNAEngine
from app.services.exceptions import ResourceNotFoundError
from app.models.impact_dna import ImpactDNA as ImpactDNAModel
from app.schemas import (
    ApiResponse,
    ApiCollectionResponse,
    ResponseMeta,
    PaginationMeta,
    CreateProjectRequest,
    ProjectResponse,
    ImpactDNA as ImpactDNASchema,
    Geography,
    BeneficiaryProfile,
    Financials,
    ProjectSector,
)

router = APIRouter()


def _to_project_response(p) -> ProjectResponse:
    """Helper to convert Project ORM model to ProjectResponse schema."""
    return ProjectResponse(
        project_id=p.public_id,
        proposal_id=p.proposal.public_id if p.proposal else None,
        ngo_id=str(p.ngo_id),
        name=p.name,
        sector=ProjectSector(p.sector),
        geographies=[
            Geography(state=g.state, district=g.district, block=g.block)
            for g in p.geographies
        ],
        beneficiary_profile=BeneficiaryProfile(target_count=1000),
        financials=Financials(
            requested_amount_paise=p.requested_amount,
            current_funding_paise=p.current_funding,
        ),
        duration_months=p.duration_months,
        impact_metrics=[],
        description=p.description,
        schema_version=p.schema_version or "project-v1",
        created_at=p.created_at.isoformat() if p.created_at else None,
        updated_at=p.updated_at.isoformat() if p.updated_at else None,
    )


def _to_impact_dna_response(dna: ImpactDNAModel) -> ImpactDNASchema:
    """Helper to convert ImpactDNA ORM model to ImpactDNA Pydantic schema."""
    missing = []
    if dna.missing_fields and isinstance(dna.missing_fields, dict):
        missing = dna.missing_fields.get("missing", [])

    return ImpactDNASchema(
        dna_id=dna.public_id,
        project_id=dna.project.public_id if dna.project else "",
        need_score=float(dna.need_score) if dna.need_score is not None else 0.0,
        expected_impact_score=float(dna.expected_impact_score) if dna.expected_impact_score is not None else 0.0,
        cost_efficiency_score=float(dna.cost_efficiency_score) if dna.cost_efficiency_score is not None else 0.0,
        evidence_strength_score=float(dna.evidence_strength_score) if dna.evidence_strength_score is not None else 0.0,
        scalability_score=float(dna.scalability_score) if dna.scalability_score is not None else 0.0,
        implementation_risk_score=float(dna.implementation_risk_score) if dna.implementation_risk_score is not None else 0.0,
        beneficiary_reach=int(dna.beneficiary_reach) if dna.beneficiary_reach is not None else 0,
        estimated_impact_per_lakh=float(dna.estimated_impact_per_lakh) if dna.estimated_impact_per_lakh is not None else 0.0,
        missing_fields=missing,
        extraction_confidence=float(dna.extraction_confidence) if dna.extraction_confidence is not None else 1.0,
        model_name=dna.model_name or "gemini-1.5-pro",
        prompt_version=dna.prompt_version or "v1.0.0",
        schema_version=dna.schema_version or "dna-v1",
    )


@router.post(
    "",
    response_model=ApiResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
def create_project(
    body: CreateProjectRequest,
    request_id: str = Depends(get_request_id),
    project_service: ProjectService = Depends(get_project_service),
) -> ApiResponse[ProjectResponse]:
    """Atomically create a new CSR project with assigned geographies and financial envelopes."""
    ngo_uuid = uuid.UUID(body.ngo_id)
    prop_uuid = uuid.UUID(body.proposal_id) if body.proposal_id else None

    project = project_service.create_project(
        ngo_id=ngo_uuid,
        name=body.name,
        sector=body.sector,
        duration_months=body.duration_months,
        requested_amount_paise=body.financials.requested_amount_paise,
        current_funding_paise=body.financials.current_funding_paise,
        geographies=[g.model_dump() for g in body.geographies],
        proposal_id=prop_uuid,
        description=body.description,
        request_id=request_id,
    )
    return ApiResponse(
        data=_to_project_response(project),
        meta=ResponseMeta(request_id=request_id),
    )


@router.get(
    "",
    response_model=ApiCollectionResponse[ProjectResponse],
    summary="List projects with pagination and filters",
)
def list_projects(
    ngo_id: Optional[uuid.UUID] = Query(None, description="Filter by NGO UUID"),
    proposal_id: Optional[uuid.UUID] = Query(None, description="Filter by proposal UUID"),
    sector: Optional[str] = Query(None, description="Filter by CSR sector"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    request_id: str = Depends(get_request_id),
    project_service: ProjectService = Depends(get_project_service),
) -> ApiCollectionResponse[ProjectResponse]:
    """List projects with deterministic pagination."""
    items, total = project_service.list_projects(
        ngo_id=ngo_id,
        proposal_id=proposal_id,
        sector=sector,
        page=page,
        page_size=page_size,
    )
    responses = [_to_project_response(p) for p in items]
    return ApiCollectionResponse(
        data=responses,
        meta=ResponseMeta(
            request_id=request_id,
            pagination=PaginationMeta(page=page, page_size=page_size, total=total),
        ),
    )


@router.get(
    "/{id}",
    response_model=ApiResponse[ProjectResponse],
    summary="Get project by public ID",
)
def get_project(
    id: str,
    request_id: str = Depends(get_request_id),
    project_service: ProjectService = Depends(get_project_service),
) -> ApiResponse[ProjectResponse]:
    """Retrieve full project details by public identifier."""
    project = project_service.get_project(id)
    return ApiResponse(
        data=_to_project_response(project),
        meta=ResponseMeta(request_id=request_id),
    )


@router.get(
    "/{id}/dna",
    response_model=ApiResponse[ImpactDNASchema],
    summary="Get project Impact DNA vector",
)
def get_project_impact_dna(
    id: str,
    request_id: str = Depends(get_request_id),
    impact_dna_service: ImpactDNAService = Depends(get_impact_dna_service),
    dna_engine: ImpactDNAEngine = Depends(get_impact_dna_engine),
) -> ApiResponse[ImpactDNASchema]:
    """Retrieve or auto-generate Impact DNA vector for a project by public identifier."""
    try:
        dna = impact_dna_service.get_dna(id)
    except ResourceNotFoundError:
        dna = impact_dna_service.generate_dna(id, engine=dna_engine, request_id=request_id)
    return ApiResponse(
        data=_to_impact_dna_response(dna),
        meta=ResponseMeta(request_id=request_id),
    )


@router.post(
    "/{id}/dna",
    response_model=ApiResponse[ImpactDNASchema],
    status_code=status.HTTP_201_CREATED,
    summary="Generate Impact DNA vector for a project",
)
def generate_project_impact_dna(
    id: str,
    request_id: str = Depends(get_request_id),
    impact_dna_service: ImpactDNAService = Depends(get_impact_dna_service),
    dna_engine: ImpactDNAEngine = Depends(get_impact_dna_engine),
) -> ApiResponse[ImpactDNASchema]:
    """Generate and persist Impact DNA vector for a project."""
    try:
        dna = impact_dna_service.get_dna(id)
    except ResourceNotFoundError:
        dna = impact_dna_service.generate_dna(id, engine=dna_engine, request_id=request_id)
    return ApiResponse(
        data=_to_impact_dna_response(dna),
        meta=ResponseMeta(request_id=request_id),
    )
