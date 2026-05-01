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
            select(func.count()).select_from(Story).where(
                Story.module_id == module_id, Story.story_type == "story"
            )
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Story)
            .where(Story.module_id == module_id, Story.story_type == "story")
            .order_by(Story.order)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_module_and_id(self, module_id: uuid.UUID, story_id: uuid.UUID) -> Story | None:
        result = await self.session.execute(
            select(Story).where(Story.module_id == module_id, Story.id == story_id, Story.story_type == "story")
        )
        return result.scalar_one_or_none()

    async def get_all_sub_stories(self, parent_story_id: uuid.UUID, skip: int, limit: int) -> tuple[list[Story], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(Story).where(Story.parent_story_id == parent_story_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Story)
            .where(Story.parent_story_id == parent_story_id)
            .order_by(Story.order)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_sub_story_by_id(self, parent_story_id: uuid.UUID, sub_story_id: uuid.UUID) -> Story | None:
        result = await self.session.execute(
            select(Story).where(
                Story.parent_story_id == parent_story_id,
                Story.id == sub_story_id,
                Story.story_type == "sub_story",
            )
        )
        return result.scalar_one_or_none()
