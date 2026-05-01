import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from app.controllers import project_plugin_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.project_plugin import ProjectPluginCreate, ProjectPluginResponse, ProjectPluginUpdate

router = APIRouter(tags=["Project Plugins"])


@router.get("/projects/{project_id}/tech-stacks/{tech_stack_id}/plugins", response_model=PaginatedResponse[ProjectPluginResponse])
async def list_plugins(
    project_id: uuid.UUID,
    tech_stack_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
):
    return await project_plugin_controller.list_plugins(project_id=project_id, tech_stack_id=tech_stack_id, page=page, size=size, db=db)


@router.get("/projects/{project_id}/plugins/{plugin_id}", response_model=ProjectPluginResponse)
async def get_plugin(project_id: uuid.UUID, plugin_id: uuid.UUID, db: DBSession):
    return await project_plugin_controller.get_plugin(project_id=project_id, plugin_id=plugin_id, db=db)


@router.post("/projects/{project_id}/plugins", response_model=ProjectPluginResponse, status_code=status.HTTP_201_CREATED)
async def create_plugin(project_id: uuid.UUID, payload: ProjectPluginCreate, db: DBSession):
    return await project_plugin_controller.create_plugin(project_id=project_id, payload=payload, db=db)


@router.patch("/projects/{project_id}/plugins/{plugin_id}", response_model=ProjectPluginResponse)
async def update_plugin(project_id: uuid.UUID, plugin_id: uuid.UUID, payload: ProjectPluginUpdate, db: DBSession):
    return await project_plugin_controller.update_plugin(project_id=project_id, plugin_id=plugin_id, payload=payload, db=db)


@router.delete("/projects/{project_id}/plugins/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plugin(project_id: uuid.UUID, plugin_id: uuid.UUID, db: DBSession) -> Response:
    return await project_plugin_controller.delete_plugin(project_id=project_id, plugin_id=plugin_id, db=db)
