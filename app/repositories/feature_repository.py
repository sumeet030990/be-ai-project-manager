import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from database.models.feature import Feature


class FeatureRepository(BaseRepository[Feature]):
    model = Feature

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all_by_epic(self, epic_id: uuid.UUID, skip: int, limit: int) -> tuple[list[Feature], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(Feature).where(Feature.epic_id == epic_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Feature)
            .where(Feature.epic_id == epic_id)
            .order_by(Feature.priority, Feature.order)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_epic_and_id(self, epic_id: uuid.UUID, feature_id: uuid.UUID) -> Feature | None:
        result = await self.session.execute(
            select(Feature).where(Feature.epic_id == epic_id, Feature.id == feature_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_epic(self, feature_id: uuid.UUID) -> Feature | None:
        result = await self.session.execute(
            select(Feature)
            .where(Feature.id == feature_id)
            .options(selectinload(Feature.epic))
        )
        return result.scalar_one_or_none()

    async def get_all_with_stories_by_epic(self, epic_id: uuid.UUID) -> list[Feature]:
        result = await self.session.execute(
            select(Feature)
            .where(Feature.epic_id == epic_id)
            .options(selectinload(Feature.stories))
            .order_by(Feature.priority, Feature.order)
        )
        return list(result.scalars().all())
