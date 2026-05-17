import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from database.models.project_ai_config import ProjectAIConfig


class ProjectAIConfigRepository(BaseRepository[ProjectAIConfig]):
    model = ProjectAIConfig

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all_by_project(
        self, project_id: uuid.UUID, skip: int, limit: int
    ) -> tuple[list[ProjectAIConfig], int]:
        count_result = await self.session.execute(
            select(func.count())
            .select_from(ProjectAIConfig)
            .where(ProjectAIConfig.project_id == project_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(ProjectAIConfig)
            .where(ProjectAIConfig.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_project_and_id(
        self, project_id: uuid.UUID, config_id: uuid.UUID
    ) -> ProjectAIConfig | None:
        result = await self.session.execute(
            select(ProjectAIConfig).where(
                ProjectAIConfig.project_id == project_id,
                ProjectAIConfig.id == config_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_default_for_project(self, project_id: uuid.UUID) -> ProjectAIConfig | None:
        result = await self.session.execute(
            select(ProjectAIConfig).where(
                ProjectAIConfig.project_id == project_id,
                ProjectAIConfig.is_default.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def unset_all_defaults(self, project_id: uuid.UUID) -> None:
        configs, _ = await self.get_all_by_project(project_id, skip=0, limit=1000)
        for c in configs:
            c.is_default = False
        await self.session.flush()
