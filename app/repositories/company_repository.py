from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    model = Company

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_email(self, email: str) -> Company | None:
        result = await self.session.execute(select(Company).where(Company.email == email))
        return result.scalar_one_or_none()

    async def get_by_gst_no(self, gst_no: str) -> Company | None:
        result = await self.session.execute(select(Company).where(Company.gst_no == gst_no))
        return result.scalar_one_or_none()
