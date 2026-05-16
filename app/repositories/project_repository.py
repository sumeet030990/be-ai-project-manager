import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from database.models.project import Project
from database.models.project_user import ProjectUser
from database.models.user import User


class ProjectRepository(BaseRepository[Project]):
    model = Project

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_name_and_company(self, name: str, company_id: uuid.UUID) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.name == name, Project.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_all_by_company(self, company_id: uuid.UUID, skip: int, limit: int) -> tuple[list[Project], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(Project).where(Project.company_id == company_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Project).where(Project.company_id == company_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_projects_by_user(self, user_id: uuid.UUID, skip: int, limit: int) -> tuple[list[Project], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(Project).join(ProjectUser, ProjectUser.project_id == Project.id).where(ProjectUser.user_id == user_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Project)
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .where(ProjectUser.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_project_user(self, project_id: uuid.UUID, user_id: uuid.UUID) -> ProjectUser | None:
        result = await self.session.execute(
            select(ProjectUser).where(ProjectUser.project_id == project_id, ProjectUser.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_existing_member_ids(self, project_id: uuid.UUID, user_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        result = await self.session.execute(
            select(ProjectUser.user_id).where(
                ProjectUser.project_id == project_id,
                ProjectUser.user_id.in_(user_ids),
            )
        )
        return set(result.scalars().all())

    async def add_users_to_project(self, project_id: uuid.UUID, user_ids: list[uuid.UUID]) -> None:
        self.session.add_all(
            [ProjectUser(project_id=project_id, user_id=uid) for uid in user_ids]
        )
        await self.session.commit()

    async def remove_user_from_project(self, project_user: ProjectUser) -> None:
        await self.session.delete(project_user)
        await self.session.commit()

    async def get_users_by_project(self, project_id: uuid.UUID, skip: int, limit: int) -> tuple[list[User], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(User).join(ProjectUser, ProjectUser.user_id == User.id).where(ProjectUser.project_id == project_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(User)
            .join(ProjectUser, ProjectUser.user_id == User.id)
            .where(ProjectUser.project_id == project_id)
            .options(selectinload(User.role), selectinload(User.company))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total
