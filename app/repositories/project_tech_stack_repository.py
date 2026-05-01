import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from database.models.project_tech_stack import ProjectTechStack


class ProjectTechStackRepository(BaseRepository[ProjectTechStack]):
    model = ProjectTechStack

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all_by_project(self, project_id: uuid.UUID, skip: int, limit: int) -> tuple[list[ProjectTechStack], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(ProjectTechStack).where(ProjectTechStack.project_id == project_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(ProjectTechStack)
            .where(ProjectTechStack.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_project_and_id(self, project_id: uuid.UUID, stack_id: uuid.UUID) -> ProjectTechStack | None:
        result = await self.session.execute(
            select(ProjectTechStack).where(
                ProjectTechStack.project_id == project_id,
                ProjectTechStack.id == stack_id,
            )
        )
        return result.scalar_one_or_none()
