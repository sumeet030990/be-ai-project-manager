import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from database.models.feature import Feature


class FeatureRepository(BaseRepository[Feature]):
    model = Feature

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all_by_project(self, project_id: uuid.UUID, skip: int, limit: int) -> tuple[list[Feature], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(Feature).where(Feature.project_id == project_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Feature)
            .where(Feature.project_id == project_id)
            .order_by(Feature.priority, Feature.order)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_project_and_id(self, project_id: uuid.UUID, feature_id: uuid.UUID) -> Feature | None:
        result = await self.session.execute(
            select(Feature).where(Feature.project_id == project_id, Feature.id == feature_id)
        )
        return result.scalar_one_or_none()
