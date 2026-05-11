import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from app.controllers import module_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.module import ModuleCreate, ModuleResponse, ModuleUpdate

router = APIRouter(prefix="/projects/{project_id}/modules", tags=["Modules"])


@router.get("", response_model=PaginatedResponse[ModuleResponse])
async def list_modules(
    project_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await module_controller.list_modules(project_id=project_id, page=page, size=size, db=db)


@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(project_id: uuid.UUID, module_id: uuid.UUID, db: DBSession):
    return await module_controller.get_module(project_id=project_id, module_id=module_id, db=db)


@router.post("", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(project_id: uuid.UUID, payload: ModuleCreate, db: DBSession):
    return await module_controller.create_module(project_id=project_id, payload=payload, db=db)


@router.patch("/{module_id}", response_model=ModuleResponse)
async def update_module(project_id: uuid.UUID, module_id: uuid.UUID, payload: ModuleUpdate, db: DBSession):
    return await module_controller.update_module(project_id=project_id, module_id=module_id, payload=payload, db=db)


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    project_id: uuid.UUID,
    module_id: uuid.UUID,
    db: DBSession,
    delete_remote: bool = Query(default=False),
) -> Response:
    return await module_controller.delete_module(project_id=project_id, module_id=module_id, db=db, delete_remote=delete_remote)
