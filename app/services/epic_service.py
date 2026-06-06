import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.repositories.epic_repository import EpicRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.epic import EpicCreate, EpicResponse, EpicUpdate
from database.models.epic import Epic


class EpicService:
    def __init__(self, session: AsyncSession):
        self.repository = EpicRepository(session)
        self.project_repository = ProjectRepository(session)
        self.user_repository = UserRepository(session)

    async def list_epics(self, project_id: uuid.UUID, page: int, size: int) -> PaginatedResponse[EpicResponse]:
        if not await self.project_repository.get_by_id(project_id):
            raise NotFoundException("Project", str(project_id))
        skip = (page - 1) * size
        items, total = await self.repository.get_all_by_project(project_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[EpicResponse.model_validate(e) for e in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_epic(self, project_id: uuid.UUID, epic_id: uuid.UUID) -> EpicResponse:
        epic = await self.repository.get_by_project_and_id(project_id, epic_id)
        if not epic:
            raise NotFoundException("Epic", str(epic_id))
        return EpicResponse.model_validate(epic)

    async def create_epic(self, project_id: uuid.UUID, payload: EpicCreate) -> EpicResponse:
        if not await self.project_repository.get_by_id(project_id):
            raise NotFoundException("Project", str(project_id))
        if not await self.user_repository.get_by_id(payload.created_by):
            raise NotFoundException("User", str(payload.created_by))
        epic = Epic(project_id=project_id, **payload.model_dump())
        epic = await self.repository.create(epic)
        return EpicResponse.model_validate(epic)

    async def update_epic(self, project_id: uuid.UUID, epic_id: uuid.UUID, payload: EpicUpdate) -> EpicResponse:
        epic = await self.repository.get_by_project_and_id(project_id, epic_id)
        if not epic:
            raise NotFoundException("Epic", str(epic_id))
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(epic, field, value)
        epic = await self.repository.update(epic)
        return EpicResponse.model_validate(epic)

    async def delete_epic(self, project_id: uuid.UUID, epic_id: uuid.UUID) -> None:
        epic = await self.repository.get_by_project_and_id(project_id, epic_id)
        if not epic:
            raise NotFoundException("Epic", str(epic_id))
        await self.repository.delete(epic)
