import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.repositories.module_repository import ModuleRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.story_repository import StoryRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.module import ModuleCreate, ModuleResponse, ModuleUpdate
from database.models.module import Module


class ModuleService:
    def __init__(self, session: AsyncSession):
        self.repository = ModuleRepository(session)
        self.project_repository = ProjectRepository(session)
        self.story_repository = StoryRepository(session)
        self.user_repository = UserRepository(session)

    async def list_modules(self, project_id: uuid.UUID, page: int, size: int) -> PaginatedResponse[ModuleResponse]:
        if not await self.project_repository.get_by_id(project_id):
            raise NotFoundException("Project", str(project_id))
        skip = (page - 1) * size
        items, total = await self.repository.get_all_by_project(project_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[ModuleResponse.model_validate(m) for m in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_module(self, project_id: uuid.UUID, module_id: uuid.UUID) -> ModuleResponse:
        module = await self.repository.get_by_project_and_id(project_id, module_id)
        if not module:
            raise NotFoundException("Module", str(module_id))
        return ModuleResponse.model_validate(module)

    async def create_module(self, project_id: uuid.UUID, payload: ModuleCreate) -> ModuleResponse:
        if not await self.project_repository.get_by_id(project_id):
            raise NotFoundException("Project", str(project_id))
        if not await self.user_repository.get_by_id(payload.created_by):
            raise NotFoundException("User", str(payload.created_by))
        module = Module(project_id=project_id, **payload.model_dump())
        module = await self.repository.create(module)
        return ModuleResponse.model_validate(module)

    async def update_module(self, project_id: uuid.UUID, module_id: uuid.UUID, payload: ModuleUpdate) -> ModuleResponse:
        module = await self.repository.get_by_project_and_id(project_id, module_id)
        if not module:
            raise NotFoundException("Module", str(module_id))
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(module, field, value)
        module = await self.repository.update(module)
        return ModuleResponse.model_validate(module)

    async def delete_module(self, project_id: uuid.UUID, module_id: uuid.UUID, delete_remote: bool = False) -> None:
        from app.services.jira_service import JiraService

        module = await self.repository.get_by_project_and_id(project_id, module_id)
        if not module:
            raise NotFoundException("Module", str(module_id))
        if delete_remote:
            linked_stories = await self.story_repository.get_jira_linked_stories_by_module(module_id)
            if linked_stories:
                jira = JiraService()
                for story in linked_stories:
                    await jira.delete_issue(story.jira_issue_key)
        await self.repository.delete(module)
