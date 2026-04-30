import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from app.controllers import company_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=PaginatedResponse[CompanyResponse])
async def list_companies(
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await company_controller.list_companies(page=page, size=size, db=db)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: uuid.UUID, db: DBSession):
    return await company_controller.get_company(company_id=company_id, db=db)


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(payload: CompanyCreate, db: DBSession):
    return await company_controller.create_company(payload=payload, db=db)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: uuid.UUID, payload: CompanyUpdate, db: DBSession):
    return await company_controller.update_company(company_id=company_id, payload=payload, db=db)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: uuid.UUID, db: DBSession) -> Response:
    return await company_controller.delete_company(company_id=company_id, db=db)
