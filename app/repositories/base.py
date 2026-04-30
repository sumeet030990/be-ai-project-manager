from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.base import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, record_id: UUID) -> ModelT | None:
        result = await self.session.execute(select(self.model).where(self.model.id == record_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> tuple[list[ModelT], int]:
        count_result = await self.session.execute(select(func.count()).select_from(self.model))
        total = count_result.scalar_one()

        result = await self.session.execute(select(self.model).offset(skip).limit(limit))
        items = list(result.scalars().all())

        return items, total

    async def create(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelT) -> ModelT:
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()
