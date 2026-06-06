import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from database.models.feature import Feature
from database.models.sprint import Sprint
from database.models.sprint_story import SprintStory
from database.models.story import Story


class SprintRepository(BaseRepository[Sprint]):
    model = Sprint

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    # ── Sprint CRUD ───────────────────────────────────────────────────────────

    async def get_all_by_project(self, project_id: uuid.UUID) -> list[Sprint]:
        result = await self.session.execute(
            select(Sprint)
            .where(Sprint.project_id == project_id)
            .order_by(Sprint.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_project_and_id(self, project_id: uuid.UUID, sprint_id: uuid.UUID) -> Sprint | None:
        result = await self.session.execute(
            select(Sprint).where(Sprint.project_id == project_id, Sprint.id == sprint_id)
        )
        return result.scalar_one_or_none()

    async def get_active_sprint(self, project_id: uuid.UUID) -> Sprint | None:
        result = await self.session.execute(
            select(Sprint).where(Sprint.project_id == project_id, Sprint.status == "active")
        )
        return result.scalar_one_or_none()

    async def get_by_jira_sprint_id(self, jira_sprint_id: int) -> Sprint | None:
        result = await self.session.execute(
            select(Sprint).where(Sprint.jira_sprint_id == jira_sprint_id)
        )
        return result.scalar_one_or_none()

    # ── Sprint-Story association ───────────────────────────────────────────────

    async def get_sprint_story_ids(self, sprint_id: uuid.UUID) -> set[uuid.UUID]:
        result = await self.session.execute(
            select(SprintStory.story_id).where(SprintStory.sprint_id == sprint_id)
        )
        return {row for (row,) in result.all()}

    async def add_stories(self, sprint_id: uuid.UUID, story_ids: list[uuid.UUID]) -> None:
        existing = await self.get_sprint_story_ids(sprint_id)
        new_entries = [
            SprintStory(sprint_id=sprint_id, story_id=sid)
            for sid in story_ids
            if sid not in existing
        ]
        if new_entries:
            self.session.add_all(new_entries)
            await self.session.flush()

    async def remove_stories(self, sprint_id: uuid.UUID, story_ids: list[uuid.UUID]) -> None:
        await self.session.execute(
            delete(SprintStory).where(
                SprintStory.sprint_id == sprint_id,
                SprintStory.story_id.in_(story_ids),
            )
        )
        await self.session.flush()

    async def remove_all_stories(self, sprint_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(SprintStory).where(SprintStory.sprint_id == sprint_id)
        )
        await self.session.flush()

    async def get_stories_in_sprint(self, sprint_id: uuid.UUID) -> list[Story]:
        story_ids_subq = select(SprintStory.story_id).where(SprintStory.sprint_id == sprint_id)
        result = await self.session.execute(
            select(Story)
            .where(Story.id.in_(story_ids_subq))
            .options(selectinload(Story.assignee))
            .order_by(Story.priority, Story.order)
        )
        return list(result.scalars().all())

    async def get_stories_in_sprint_with_feature(self, sprint_id: uuid.UUID) -> list[Story]:
        story_ids_subq = select(SprintStory.story_id).where(SprintStory.sprint_id == sprint_id)
        result = await self.session.execute(
            select(Story)
            .where(Story.id.in_(story_ids_subq))
            .options(selectinload(Story.assignee), selectinload(Story.feature))
            .order_by(Story.priority, Story.order)
        )
        return list(result.scalars().all())

    # ── Backlog ───────────────────────────────────────────────────────────────

    async def get_backlog_stories(self, project_id: uuid.UUID) -> list[Story]:
        """Stories belonging to project features that are not assigned to any sprint."""
        all_sprint_story_ids_subq = select(SprintStory.story_id)
        feature_ids_subq = select(Feature.id).where(Feature.project_id == project_id)

        result = await self.session.execute(
            select(Story)
            .where(
                Story.feature_id.in_(feature_ids_subq),
                ~Story.id.in_(all_sprint_story_ids_subq),
            )
            .options(selectinload(Story.assignee), selectinload(Story.feature))
            .order_by(Story.priority, Story.order)
        )
        return list(result.scalars().all())

    async def get_story_ids_assigned_to_any_sprint(self, story_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        result = await self.session.execute(
            select(SprintStory.story_id).where(SprintStory.story_id.in_(story_ids))
        )
        return {row for (row,) in result.all()}

    async def count_stories_in_sprint(self, sprint_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(SprintStory).where(SprintStory.sprint_id == sprint_id)
        )
        return result.scalar_one()
