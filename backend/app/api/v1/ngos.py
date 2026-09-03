import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_request_id
from app.db.session import get_db
from app.repositories import NGORepository
from app.schemas import (
    ApiCollectionResponse,
    ResponseMeta,
    PaginationMeta,
)


router = APIRouter()


class NGOResponse(BaseModel):
    """Schema representing a registered NGO partner."""
    id: str = Field(..., description="Canonical NGO UUID identifier")
    name: str = Field(..., description="Official NGO organization name")
    external_id: Optional[str] = Field(None, description="External reference ID (e.g. NGO-0001)")
    registration_number: Optional[str] = Field(None, description="Statutory registration number")


@router.get(
    "",
    response_model=ApiCollectionResponse[NGOResponse],
    summary="List registered NGOs with pagination",
)
def list_ngos(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    request_id: str = Depends(get_request_id),
    session: Session = Depends(get_db),
) -> ApiCollectionResponse[NGOResponse]:
    """Retrieve list of registered NGO partner entities from PostgreSQL."""
    repo = NGORepository(session)
    items, total = repo.list(page=page, page_size=page_size)
    responses = [
        NGOResponse(
            id=str(ngo.id),
            name=ngo.name,
            external_id=ngo.external_id,
            registration_number=ngo.registration_number,
        )
        for ngo in items
    ]
    return ApiCollectionResponse(
        data=responses,
        meta=ResponseMeta(
            request_id=request_id,
            pagination=PaginationMeta(page=page, page_size=page_size, total=total),
        ),
    )
