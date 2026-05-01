import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.repositories.project_repository import ProjectRepository
from app.repositories.project_plugin_repository import ProjectPluginRepository
from app.repositories.project_tech_stack_repository import ProjectTechStackRepository
from app.schemas.common import PaginatedResponse
from app.schemas.project_plugin import ProjectPluginCreate, ProjectPluginResponse, ProjectPluginUpdate
from database.models.project_plugin import ProjectPlugin


class ProjectPluginService:
    def __init__(self, session: AsyncSession):
        self.repository = ProjectPluginRepository(session)
        self.project_repository = ProjectRepository(session)
        self.tech_stack_repository = ProjectTechStackRepository(session)

    async def _get_project_or_404(self, project_id: uuid.UUID) -> None:
        if not await self.project_repository.get_by_id(project_id):
            raise NotFoundException("Project", str(project_id))

    async def _validate_tech_stack(self, project_id: uuid.UUID, tech_stack_id: uuid.UUID) -> None:
        stack = await self.tech_stack_repository.get_by_project_and_id(project_id, tech_stack_id)
        if not stack:
            raise BadRequestException(f"TechStack '{tech_stack_id}' does not belong to project '{project_id}'.")

    async def list_plugins(self, project_id: uuid.UUID, page: int, size: int, tech_stack_id: uuid.UUID) -> PaginatedResponse[ProjectPluginResponse]:
        await self._get_project_or_404(project_id)
        await self._validate_tech_stack(project_id, tech_stack_id)
        skip = (page - 1) * size
        items, total = await self.repository.get_all_by_project(project_id, skip=skip, limit=size, tech_stack_id=tech_stack_id)
        return PaginatedResponse(
            items=[ProjectPluginResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_plugin(self, project_id: uuid.UUID, plugin_id: uuid.UUID) -> ProjectPluginResponse:
        await self._get_project_or_404(project_id)
        plugin = await self.repository.get_by_project_and_id(project_id, plugin_id)
        if not plugin:
            raise NotFoundException("Plugin", str(plugin_id))
        return ProjectPluginResponse.model_validate(plugin)

    async def create_plugin(self, project_id: uuid.UUID, payload: ProjectPluginCreate) -> ProjectPluginResponse:
        await self._get_project_or_404(project_id)
        await self._validate_tech_stack(project_id, payload.tech_stack_id)
        plugin = ProjectPlugin(project_id=project_id, **payload.model_dump())
        plugin = await self.repository.create(plugin)
        return ProjectPluginResponse.model_validate(plugin)

    async def update_plugin(self, project_id: uuid.UUID, plugin_id: uuid.UUID, payload: ProjectPluginUpdate) -> ProjectPluginResponse:
        await self._get_project_or_404(project_id)
        plugin = await self.repository.get_by_project_and_id(project_id, plugin_id)
        if not plugin:
            raise NotFoundException("Plugin", str(plugin_id))
        update_data = payload.model_dump(exclude_unset=True)
        if "tech_stack_id" in update_data:
            await self._validate_tech_stack(project_id, update_data["tech_stack_id"])
        for field, value in update_data.items():
            setattr(plugin, field, value)
        plugin = await self.repository.update(plugin)
        return ProjectPluginResponse.model_validate(plugin)

    async def delete_plugin(self, project_id: uuid.UUID, plugin_id: uuid.UUID) -> None:
        await self._get_project_or_404(project_id)
        plugin = await self.repository.get_by_project_and_id(project_id, plugin_id)
        if not plugin:
            raise NotFoundException("Plugin", str(plugin_id))
        await self.repository.delete(plugin)
