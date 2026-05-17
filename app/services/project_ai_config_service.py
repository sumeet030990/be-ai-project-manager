import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_api_key, encrypt_api_key, mask_api_key
from app.core.exceptions import NotFoundException
from app.repositories.project_ai_config_repository import ProjectAIConfigRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.common import PaginatedResponse
from app.schemas.project_ai_config import (
    ProjectAIConfigCreate,
    ProjectAIConfigResponse,
    ProjectAIConfigUpdate,
)
from database.models.project_ai_config import ProjectAIConfig


def _to_response(config: ProjectAIConfig) -> ProjectAIConfigResponse:
    plaintext = decrypt_api_key(config.api_key)
    return ProjectAIConfigResponse(
        id=config.id,
        project_id=config.project_id,
        provider=config.provider,
        api_key_masked=mask_api_key(plaintext),
        model_name=config.model_name,
        is_default=config.is_default,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


class ProjectAIConfigService:
    def __init__(self, session: AsyncSession):
        self.repository = ProjectAIConfigRepository(session)
        self.project_repository = ProjectRepository(session)

    async def _get_project_or_404(self, project_id: uuid.UUID):
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        return project

    async def _get_config_or_404(self, project_id: uuid.UUID, config_id: uuid.UUID) -> ProjectAIConfig:
        config = await self.repository.get_by_project_and_id(project_id, config_id)
        if not config:
            raise NotFoundException("ProjectAIConfig", str(config_id))
        return config

    async def list_configs(
        self, project_id: uuid.UUID, page: int, size: int
    ) -> PaginatedResponse[ProjectAIConfigResponse]:
        await self._get_project_or_404(project_id)
        skip = (page - 1) * size
        items, total = await self.repository.get_all_by_project(project_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[_to_response(c) for c in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_config(self, project_id: uuid.UUID, config_id: uuid.UUID) -> ProjectAIConfigResponse:
        config = await self._get_config_or_404(project_id, config_id)
        return _to_response(config)

    async def create_config(
        self, project_id: uuid.UUID, payload: ProjectAIConfigCreate
    ) -> ProjectAIConfigResponse:
        await self._get_project_or_404(project_id)

        if payload.is_default:
            await self.repository.unset_all_defaults(project_id)

        config = ProjectAIConfig(
            project_id=project_id,
            provider=payload.provider,
            api_key=encrypt_api_key(payload.api_key),
            model_name=payload.model_name,
            is_default=payload.is_default,
        )
        config = await self.repository.create(config)
        return _to_response(config)

    async def update_config(
        self, project_id: uuid.UUID, config_id: uuid.UUID, payload: ProjectAIConfigUpdate
    ) -> ProjectAIConfigResponse:
        config = await self._get_config_or_404(project_id, config_id)

        if payload.is_default is True and not config.is_default:
            await self.repository.unset_all_defaults(project_id)

        data = payload.model_dump(exclude_unset=True)
        if "api_key" in data and data["api_key"]:
            data["api_key"] = encrypt_api_key(data["api_key"])

        for field, value in data.items():
            setattr(config, field, value)

        config = await self.repository.update(config)
        return _to_response(config)

    async def delete_config(self, project_id: uuid.UUID, config_id: uuid.UUID) -> None:
        config = await self._get_config_or_404(project_id, config_id)
        await self.repository.delete(config)
