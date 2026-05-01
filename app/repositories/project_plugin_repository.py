import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from database.models.project_plugin import ProjectPlugin


class ProjectPluginRepository(BaseRepository[ProjectPlugin]):
    model = ProjectPlugin

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all_by_project(
        self,
        project_id: uuid.UUID,
        skip: int,
        limit: int,
        tech_stack_id: uuid.UUID | None = None,
    ) -> tuple[list[ProjectPlugin], int]:
        filters = [ProjectPlugin.project_id == project_id]
        if tech_stack_id is not None:
            filters.append(ProjectPlugin.tech_stack_id == tech_stack_id)

        count_result = await self.session.execute(
            select(func.count()).select_from(ProjectPlugin).where(*filters)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(ProjectPlugin).where(*filters).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_project_and_id(self, project_id: uuid.UUID, plugin_id: uuid.UUID) -> ProjectPlugin | None:
        result = await self.session.execute(
            select(ProjectPlugin).where(
                ProjectPlugin.project_id == project_id,
                ProjectPlugin.id == plugin_id,
            )
        )
        return result.scalar_one_or_none()
