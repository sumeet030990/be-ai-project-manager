import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from database.models.epic import Epic


class EpicRepository(BaseRepository[Epic]):
    model = Epic

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all_by_project(self, project_id: uuid.UUID, skip: int, limit: int) -> tuple[list[Epic], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(Epic).where(Epic.project_id == project_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Epic)
            .where(Epic.project_id == project_id)
            .order_by(Epic.priority, Epic.order)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_project_and_id(self, project_id: uuid.UUID, epic_id: uuid.UUID) -> Epic | None:
        result = await self.session.execute(
            select(Epic).where(Epic.project_id == project_id, Epic.id == epic_id)
        )
        return result.scalar_one_or_none()
