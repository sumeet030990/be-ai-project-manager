import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.repositories.project_repository import ProjectRepository
from app.repositories.project_tech_stack_repository import ProjectTechStackRepository
from app.schemas.common import PaginatedResponse
from app.schemas.project_tech_stack import ProjectTechStackCreate, ProjectTechStackResponse, ProjectTechStackUpdate
from database.models.project_tech_stack import ProjectTechStack


class ProjectTechStackService:
    def __init__(self, session: AsyncSession):
        self.repository = ProjectTechStackRepository(session)
        self.project_repository = ProjectRepository(session)

    async def _get_project_or_404(self, project_id: uuid.UUID) -> None:
        if not await self.project_repository.get_by_id(project_id):
            raise NotFoundException("Project", str(project_id))

    async def list_tech_stacks(self, project_id: uuid.UUID, page: int, size: int) -> PaginatedResponse[ProjectTechStackResponse]:
        await self._get_project_or_404(project_id)
        skip = (page - 1) * size
        items, total = await self.repository.get_all_by_project(project_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[ProjectTechStackResponse.model_validate(s) for s in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_tech_stack(self, project_id: uuid.UUID, stack_id: uuid.UUID) -> ProjectTechStackResponse:
        await self._get_project_or_404(project_id)
        stack = await self.repository.get_by_project_and_id(project_id, stack_id)
        if not stack:
            raise NotFoundException("TechStack", str(stack_id))
        return ProjectTechStackResponse.model_validate(stack)

    async def create_tech_stack(self, project_id: uuid.UUID, payload: ProjectTechStackCreate) -> ProjectTechStackResponse:
        await self._get_project_or_404(project_id)
        stack = ProjectTechStack(project_id=project_id, **payload.model_dump())
        stack = await self.repository.create(stack)
        return ProjectTechStackResponse.model_validate(stack)

    async def update_tech_stack(self, project_id: uuid.UUID, stack_id: uuid.UUID, payload: ProjectTechStackUpdate) -> ProjectTechStackResponse:
        await self._get_project_or_404(project_id)
        stack = await self.repository.get_by_project_and_id(project_id, stack_id)
        if not stack:
            raise NotFoundException("TechStack", str(stack_id))
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(stack, field, value)
        stack = await self.repository.update(stack)
        return ProjectTechStackResponse.model_validate(stack)

    async def delete_tech_stack(self, project_id: uuid.UUID, stack_id: uuid.UUID) -> None:
        await self._get_project_or_404(project_id)
        stack = await self.repository.get_by_project_and_id(project_id, stack_id)
        if not stack:
            raise NotFoundException("TechStack", str(stack_id))
        await self.repository.delete(stack)
