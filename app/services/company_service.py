import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from database.models.company import Company
from app.repositories.company_repository import CompanyRepository
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate


class CompanyService:
    def __init__(self, session: AsyncSession):
        self.repository = CompanyRepository(session)

    async def get_company(self, company_id: uuid.UUID) -> CompanyResponse:
        company = await self.repository.get_by_id(company_id)
        if not company:
            raise NotFoundException("Company", str(company_id))
        return CompanyResponse.model_validate(company)

    async def list_companies(self, page: int, size: int) -> PaginatedResponse[CompanyResponse]:
        skip = (page - 1) * size
        items, total = await self.repository.get_all(skip=skip, limit=size)
        return PaginatedResponse(
            items=[CompanyResponse.model_validate(c) for c in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def create_company(self, payload: CompanyCreate) -> CompanyResponse:
        if await self.repository.get_by_email(payload.email):
            raise ConflictException(f"Email '{payload.email}' is already registered.")
        if payload.gst_no and await self.repository.get_by_gst_no(payload.gst_no):
            raise ConflictException(f"GST number '{payload.gst_no}' is already registered.")

        company = Company(**payload.model_dump())
        company = await self.repository.create(company)
        return CompanyResponse.model_validate(company)

    async def update_company(self, company_id: uuid.UUID, payload: CompanyUpdate) -> CompanyResponse:
        company = await self.repository.get_by_id(company_id)
        if not company:
            raise NotFoundException("Company", str(company_id))

        update_data = payload.model_dump(exclude_unset=True)

        if "email" in update_data:
            existing = await self.repository.get_by_email(update_data["email"])
            if existing and existing.id != company_id:
                raise ConflictException(f"Email '{update_data['email']}' is already registered.")

        if "gst_no" in update_data and update_data["gst_no"]:
            existing = await self.repository.get_by_gst_no(update_data["gst_no"])
            if existing and existing.id != company_id:
                raise ConflictException(f"GST number '{update_data['gst_no']}' is already registered.")

        for field, value in update_data.items():
            setattr(company, field, value)

        company = await self.repository.update(company)
        return CompanyResponse.model_validate(company)

    async def delete_company(self, company_id: uuid.UUID) -> None:
        company = await self.repository.get_by_id(company_id)
        if not company:
            raise NotFoundException("Company", str(company_id))
        await self.repository.delete(company)
