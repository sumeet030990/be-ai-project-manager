import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from database.models.story import Story


class StoryRepository(BaseRepository[Story]):
    model = Story

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _with_assignee(self, q):
        return q.options(selectinload(Story.assignee))

    async def _get_by_id_with_assignee(self, story_id: uuid.UUID) -> Story | None:
        result = await self.session.execute(
            self._with_assignee(select(Story).where(Story.id == story_id))
        )
        return result.scalar_one_or_none()

    async def create(self, instance: Story) -> Story:
        self.session.add(instance)
        await self.session.flush()
        return await self._get_by_id_with_assignee(instance.id)

    async def update(self, instance: Story) -> Story:
        await self.session.flush()
        return await self._get_by_id_with_assignee(instance.id)

    async def get_all_by_feature(self, feature_id: uuid.UUID, skip: int, limit: int) -> tuple[list[Story], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(Story).where(Story.feature_id == feature_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            self._with_assignee(
                select(Story)
                .where(Story.feature_id == feature_id)
                .order_by(Story.priority, Story.order)
                .offset(skip)
                .limit(limit)
            )
        )
        return list(result.scalars().all()), total

    async def get_by_feature_and_id(self, feature_id: uuid.UUID, story_id: uuid.UUID) -> Story | None:
        result = await self.session.execute(
            self._with_assignee(
                select(Story).where(Story.feature_id == feature_id, Story.id == story_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_jira_linked_stories_by_feature(self, feature_id: uuid.UUID) -> list[Story]:
        result = await self.session.execute(
            select(Story).where(Story.feature_id == feature_id, Story.jira_issue_key.isnot(None))
        )
        return list(result.scalars().all())

    async def get_by_jira_keys(self, keys: list[str]) -> list[Story]:
        result = await self.session.execute(
            self._with_assignee(select(Story).where(Story.jira_issue_key.in_(keys)))
        )
        return list(result.scalars().all())

    async def get_existing_jira_keys(self) -> set[str]:
        result = await self.session.execute(
            select(Story.jira_issue_key).where(Story.jira_issue_key.isnot(None))
        )
        return {row for (row,) in result.all()}

    async def bulk_create(self, stories: list[Story]) -> list[Story]:
        self.session.add_all(stories)
        await self.session.flush()
        for story in stories:
            await self.session.refresh(story)
        return stories
