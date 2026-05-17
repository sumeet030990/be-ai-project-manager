import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.project_ai_config import (
    ProjectAIConfigCreate,
    ProjectAIConfigResponse,
    ProjectAIConfigUpdate,
)
from app.services.project_ai_config_service import ProjectAIConfigService


async def list_ai_configs(
    project_id: uuid.UUID, page: int, size: int, db: DBSession
) -> PaginatedResponse[ProjectAIConfigResponse]:
    return await ProjectAIConfigService(db).list_configs(project_id=project_id, page=page, size=size)


async def get_ai_config(
    project_id: uuid.UUID, config_id: uuid.UUID, db: DBSession
) -> ProjectAIConfigResponse:
    return await ProjectAIConfigService(db).get_config(project_id=project_id, config_id=config_id)


async def create_ai_config(
    project_id: uuid.UUID, payload: ProjectAIConfigCreate, db: DBSession
) -> ProjectAIConfigResponse:
    return await ProjectAIConfigService(db).create_config(project_id=project_id, payload=payload)


async def update_ai_config(
    project_id: uuid.UUID, config_id: uuid.UUID, payload: ProjectAIConfigUpdate, db: DBSession
) -> ProjectAIConfigResponse:
    return await ProjectAIConfigService(db).update_config(
        project_id=project_id, config_id=config_id, payload=payload
    )


async def delete_ai_config(
    project_id: uuid.UUID, config_id: uuid.UUID, db: DBSession
) -> Response:
    await ProjectAIConfigService(db).delete_config(project_id=project_id, config_id=config_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
