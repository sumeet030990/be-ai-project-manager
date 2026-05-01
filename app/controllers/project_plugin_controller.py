import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.project_plugin import ProjectPluginCreate, ProjectPluginResponse, ProjectPluginUpdate
from app.services.project_plugin_service import ProjectPluginService


async def list_plugins(project_id: uuid.UUID, page: int, size: int, tech_stack_id: uuid.UUID, db: DBSession) -> PaginatedResponse[ProjectPluginResponse]:
    return await ProjectPluginService(db).list_plugins(project_id=project_id, page=page, size=size, tech_stack_id=tech_stack_id)


async def get_plugin(project_id: uuid.UUID, plugin_id: uuid.UUID, db: DBSession) -> ProjectPluginResponse:
    return await ProjectPluginService(db).get_plugin(project_id=project_id, plugin_id=plugin_id)


async def create_plugin(project_id: uuid.UUID, payload: ProjectPluginCreate, db: DBSession) -> ProjectPluginResponse:
    return await ProjectPluginService(db).create_plugin(project_id=project_id, payload=payload)


async def update_plugin(project_id: uuid.UUID, plugin_id: uuid.UUID, payload: ProjectPluginUpdate, db: DBSession) -> ProjectPluginResponse:
    return await ProjectPluginService(db).update_plugin(project_id=project_id, plugin_id=plugin_id, payload=payload)


async def delete_plugin(project_id: uuid.UUID, plugin_id: uuid.UUID, db: DBSession) -> Response:
    await ProjectPluginService(db).delete_plugin(project_id=project_id, plugin_id=plugin_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
