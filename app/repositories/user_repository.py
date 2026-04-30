from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _base_query(self):
        return select(User).options(selectinload(User.role), selectinload(User.company))

    async def get_by_id(self, record_id: UUID) -> User | None:
        result = await self.session.execute(
            self._base_query().where(User.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(User)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            self._base_query().offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def create(self, instance: User) -> User:
        self.session.add(instance)
        await self.session.flush()
        return await self.get_by_id(instance.id)

    async def update(self, instance: User) -> User:
        await self.session.flush()
        return await self.get_by_id(instance.id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_contact_no(self, contact_no: str) -> User | None:
        result = await self.session.execute(select(User).where(User.contact_no == contact_no))
        return result.scalar_one_or_none()
