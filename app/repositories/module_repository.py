import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from database.models.module import Module


class ModuleRepository(BaseRepository[Module]):
    model = Module

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all_by_project(self, project_id: uuid.UUID, skip: int, limit: int) -> tuple[list[Module], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(Module).where(Module.project_id == project_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Module)
            .where(Module.project_id == project_id)
            .order_by(Module.order)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_project_and_id(self, project_id: uuid.UUID, module_id: uuid.UUID) -> Module | None:
        result = await self.session.execute(
            select(Module).where(Module.project_id == project_id, Module.id == module_id)
        )
        return result.scalar_one_or_none()
