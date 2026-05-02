import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from database.models.story import Story


class StoryRepository(BaseRepository[Story]):
    model = Story

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all_by_module(self, module_id: uuid.UUID, skip: int, limit: int) -> tuple[list[Story], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(Story).where(Story.module_id == module_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Story)
            .where(Story.module_id == module_id)
            .order_by(Story.order)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_module_and_id(self, module_id: uuid.UUID, story_id: uuid.UUID) -> Story | None:
        result = await self.session.execute(
            select(Story).where(Story.module_id == module_id, Story.id == story_id)
        )
        return result.scalar_one_or_none()

    async def bulk_create(self, stories: list[Story]) -> list[Story]:
        self.session.add_all(stories)
        await self.session.flush()
        for story in stories:
            await self.session.refresh(story)
        return stories
