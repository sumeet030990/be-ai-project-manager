import uuid

from fastapi import APIRouter, Query
from fastapi.responses import Response

import app.controllers.project_ai_config_controller as controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.project_ai_config import (
    ProjectAIConfigCreate,
    ProjectAIConfigResponse,
    ProjectAIConfigUpdate,
)

router = APIRouter(prefix="/projects/{project_id}/ai-configs", tags=["AI Config"])


@router.get("", response_model=PaginatedResponse[ProjectAIConfigResponse])
async def list_ai_configs(
    project_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await controller.list_ai_configs(project_id=project_id, page=page, size=size, db=db)


@router.post("", response_model=ProjectAIConfigResponse, status_code=201)
async def create_ai_config(
    project_id: uuid.UUID,
    payload: ProjectAIConfigCreate,
    db: DBSession,
):
    return await controller.create_ai_config(project_id=project_id, payload=payload, db=db)


@router.get("/{config_id}", response_model=ProjectAIConfigResponse)
async def get_ai_config(
    project_id: uuid.UUID,
    config_id: uuid.UUID,
    db: DBSession,
):
    return await controller.get_ai_config(project_id=project_id, config_id=config_id, db=db)


@router.patch("/{config_id}", response_model=ProjectAIConfigResponse)
async def update_ai_config(
    project_id: uuid.UUID,
    config_id: uuid.UUID,
    payload: ProjectAIConfigUpdate,
    db: DBSession,
):
    return await controller.update_ai_config(
        project_id=project_id, config_id=config_id, payload=payload, db=db
    )


@router.delete("/{config_id}", status_code=204, response_class=Response)
async def delete_ai_config(
    project_id: uuid.UUID,
    config_id: uuid.UUID,
    db: DBSession,
):
    return await controller.delete_ai_config(project_id=project_id, config_id=config_id, db=db)
