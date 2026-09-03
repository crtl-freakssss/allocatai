import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    get_request_id,
    get_proposal_service,
    get_document_service,
    get_extraction_service,
    get_extraction_engine,
)
from app.services import (
    ProposalService,
    DocumentService,
    ExtractionService,
    ExtractionEngine,
)
from app.schemas import (
    ApiResponse,
    ApiCollectionResponse,
    ResponseMeta,
    PaginationMeta,
    CreateProposalRequest,
    CreateProposalResponse,
    ProposalResponse,
    UploadDocumentRequest,
    CreateDocumentResponse,
    DocumentResponse,
    ExtractProposalRequest,
    ExtractProposalResponse,
    ProposalStatus,
)

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse[CreateProposalResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new proposal",
)
def create_proposal(
    body: CreateProposalRequest,
    request_id: str = Depends(get_request_id),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> ApiResponse[CreateProposalResponse]:
    """Ingest a new project proposal and assign an authoritative PRO identifier."""
    ngo_uuid = uuid.UUID(body.ngo_id)
    proposal = proposal_service.create_proposal(
        ngo_id=ngo_uuid,
        title=body.title,
        source_type=body.source_type,
        request_id=request_id,
    )
    return ApiResponse(
        data=CreateProposalResponse(
            proposal_id=proposal.public_id,
            status=ProposalStatus(proposal.status),
        ),
        meta=ResponseMeta(request_id=request_id),
    )


@router.get(
    "",
    response_model=ApiCollectionResponse[ProposalResponse],
    summary="List proposals with pagination and filters",
)
def list_proposals(
    ngo_id: Optional[uuid.UUID] = Query(None, description="Filter by NGO UUID"),
    status: Optional[str] = Query(None, description="Filter by proposal lifecycle status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    request_id: str = Depends(get_request_id),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> ApiCollectionResponse[ProposalResponse]:
    """Retrieve proposals ordered deterministically with pagination."""
    items, total = proposal_service.list_proposals(
        ngo_id=ngo_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    responses = [
        ProposalResponse(
            proposal_id=p.public_id,
            ngo_id=str(p.ngo_id),
            title=p.title,
            status=ProposalStatus(p.status),
            source_type=p.source_type,
            created_at=p.created_at.isoformat() if p.created_at else "",
            updated_at=p.updated_at.isoformat() if p.updated_at else None,
        )
        for p in items
    ]
    return ApiCollectionResponse(
        data=responses,
        meta=ResponseMeta(
            request_id=request_id,
            pagination=PaginationMeta(page=page, page_size=page_size, total=total),
        ),
    )


@router.get(
    "/{id}",
    response_model=ApiResponse[ProposalResponse],
    summary="Get proposal by public ID",
)
def get_proposal(
    id: str,
    request_id: str = Depends(get_request_id),
    proposal_service: ProposalService = Depends(get_proposal_service),
) -> ApiResponse[ProposalResponse]:
    """Retrieve details of a single proposal by its public ID."""
    proposal = proposal_service.get_proposal(id)
    return ApiResponse(
        data=ProposalResponse(
            proposal_id=proposal.public_id,
            ngo_id=str(proposal.ngo_id),
            title=proposal.title,
            status=ProposalStatus(proposal.status),
            source_type=proposal.source_type,
            created_at=proposal.created_at.isoformat() if proposal.created_at else "",
            updated_at=proposal.updated_at.isoformat() if proposal.updated_at else None,
        ),
        meta=ResponseMeta(request_id=request_id),
    )


@router.post(
    "/{id}/documents",
    response_model=ApiResponse[CreateDocumentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Attach document metadata to a proposal",
)
def attach_document(
    id: str,
    body: UploadDocumentRequest,
    request_id: str = Depends(get_request_id),
    document_service: DocumentService = Depends(get_document_service),
) -> ApiResponse[CreateDocumentResponse]:
    """Attach document metadata and SHA-256 fingerprint to an existing proposal."""
    doc = document_service.attach_document(
        proposal_public_id=id,
        filename=body.filename,
        mime_type=body.mime_type,
        storage_key=body.storage_key,
        file_size_bytes=body.file_size_bytes,
        sha256=body.sha256,
        request_id=request_id,
    )
    return ApiResponse(
        data=CreateDocumentResponse(
            document_id=doc.public_id,
            proposal_id=id,
            filename=doc.filename,
            status=ProposalStatus.UPLOADED,
        ),
        meta=ResponseMeta(request_id=request_id),
    )


@router.get(
    "/{id}/documents",
    response_model=ApiCollectionResponse[DocumentResponse],
    summary="List documents attached to a proposal",
)
def list_proposal_documents(
    id: str,
    request_id: str = Depends(get_request_id),
    document_service: DocumentService = Depends(get_document_service),
) -> ApiCollectionResponse[DocumentResponse]:
    """List all documents attached to the specified proposal."""
    docs = document_service.list_proposal_documents(proposal_public_id=id)
    responses = [
        DocumentResponse(
            document_id=d.public_id,
            proposal_id=id,
            filename=d.filename,
            mime_type=d.mime_type,
            file_size_bytes=d.file_size_bytes,
            sha256=d.sha256,
            created_at=d.created_at.isoformat() if d.created_at else "",
        )
        for d in docs
    ]
    return ApiCollectionResponse(
        data=responses,
        meta=ResponseMeta(
            request_id=request_id,
            pagination=PaginationMeta(page=1, page_size=len(responses), total=len(responses)),
        ),
    )


@router.post(
    "/{id}/extract",
    response_model=ApiResponse[ExtractProposalResponse],
    summary="Trigger AI extraction on an uploaded proposal document",
)
def extract_proposal(
    id: str,
    body: ExtractProposalRequest,
    request_id: str = Depends(get_request_id),
    extraction_service: ExtractionService = Depends(get_extraction_service),
    engine: ExtractionEngine = Depends(get_extraction_engine),
) -> ApiResponse[ExtractProposalResponse]:
    """Orchestrate automated document extraction, project creation, and lifecycle progression."""
    extraction_result, project = extraction_service.extract_proposal(
        proposal_public_id=id,
        document_public_id=body.document_id,
        engine=engine,
        request_id=request_id,
    )
    return ApiResponse(
        data=ExtractProposalResponse(
            proposal_id=id,
            status=ProposalStatus.EXTRACTED if not extraction_result.missing_fields else ProposalStatus.VALIDATION_REQUIRED,
            project_id=project.public_id,
            extraction_confidence=float(extraction_result.extraction_confidence),
            missing_fields=extraction_result.missing_fields,
        ),
        meta=ResponseMeta(request_id=request_id),
    )
