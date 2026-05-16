import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.repositories.company_repository import CompanyRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectUserCreate
from app.schemas.user import UserResponse
from database.models.project import Project


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.repository = ProjectRepository(session)
        self.company_repository = CompanyRepository(session)
        self.user_repository = UserRepository(session)

    async def get_project(self, project_id: uuid.UUID) -> ProjectResponse:
        project = await self.repository.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        return ProjectResponse.model_validate(project)

    async def list_projects(self, page: int, size: int, company_id: uuid.UUID | None) -> PaginatedResponse[ProjectResponse]:
        skip = (page - 1) * size
        if company_id:
            items, total = await self.repository.get_all_by_company(company_id, skip=skip, limit=size)
        else:
            items, total = await self.repository.get_all(skip=skip, limit=size)
        return PaginatedResponse(
            items=[ProjectResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def create_project(self, payload: ProjectCreate) -> ProjectResponse:
        if not await self.company_repository.get_by_id(payload.company_id):
            raise NotFoundException("Company", str(payload.company_id))
        if not await self.user_repository.get_by_id(payload.created_by):
            raise NotFoundException("User", str(payload.created_by))
        if await self.repository.get_by_name_and_company(payload.name, payload.company_id):
            raise ConflictException(f"Project '{payload.name}' already exists in this company.")

        project = Project(**payload.model_dump())
        project = await self.repository.create(project)
        return ProjectResponse.model_validate(project)

    async def update_project(self, project_id: uuid.UUID, payload: ProjectUpdate) -> ProjectResponse:
        project = await self.repository.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))

        update_data = payload.model_dump(exclude_unset=True)

        if "name" in update_data:
            existing = await self.repository.get_by_name_and_company(update_data["name"], project.company_id)
            if existing and existing.id != project_id:
                raise ConflictException(f"Project '{update_data['name']}' already exists in this company.")

        for field, value in update_data.items():
            setattr(project, field, value)

        project = await self.repository.update(project)
        return ProjectResponse.model_validate(project)

    async def list_project_users(self, project_id: uuid.UUID, page: int, size: int) -> PaginatedResponse[UserResponse]:
        if not await self.repository.get_by_id(project_id):
            raise NotFoundException("Project", str(project_id))
        skip = (page - 1) * size
        items, total = await self.repository.get_users_by_project(project_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[UserResponse.model_validate(u) for u in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def add_project_users(self, project_id: uuid.UUID, payload: ProjectUserCreate) -> list[UserResponse]:
        if not await self.repository.get_by_id(project_id):
            raise NotFoundException("Project", str(project_id))

        users = []
        for uid in payload.user_ids:
            user = await self.user_repository.get_by_id(uid)
            if not user:
                raise NotFoundException("User", str(uid))
            users.append(user)

        existing_ids = await self.repository.get_existing_member_ids(project_id, payload.user_ids)
        new_user_ids = [u.id for u in users if u.id not in existing_ids]

        if new_user_ids:
            await self.repository.add_users_to_project(project_id, new_user_ids)

        return [UserResponse.model_validate(u) for u in users if u.id in set(new_user_ids)]

    async def remove_project_user(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        if not await self.repository.get_by_id(project_id):
            raise NotFoundException("Project", str(project_id))
        project_user = await self.repository.get_project_user(project_id, user_id)
        if not project_user:
            raise NotFoundException("ProjectUser", f"{project_id}/{user_id}")
        await self.repository.remove_user_from_project(project_user)

    async def delete_project(self, project_id: uuid.UUID) -> None:
        project = await self.repository.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        await self.repository.delete(project)
