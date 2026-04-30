import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.services.company_service import CompanyService


async def list_companies(page: int, size: int, db: DBSession) -> PaginatedResponse[CompanyResponse]:
    return await CompanyService(db).list_companies(page=page, size=size)


async def get_company(company_id: uuid.UUID, db: DBSession) -> CompanyResponse:
    return await CompanyService(db).get_company(company_id)


async def create_company(payload: CompanyCreate, db: DBSession) -> CompanyResponse:
    return await CompanyService(db).create_company(payload)


async def update_company(company_id: uuid.UUID, payload: CompanyUpdate, db: DBSession) -> CompanyResponse:
    return await CompanyService(db).update_company(company_id, payload)


async def delete_company(company_id: uuid.UUID, db: DBSession) -> Response:
    await CompanyService(db).delete_company(company_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
