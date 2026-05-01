import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.module import ModuleCreate, ModuleResponse, ModuleUpdate
from app.services.module_service import ModuleService


async def list_modules(project_id: uuid.UUID, page: int, size: int, db: DBSession) -> PaginatedResponse[ModuleResponse]:
    return await ModuleService(db).list_modules(project_id=project_id, page=page, size=size)


async def get_module(project_id: uuid.UUID, module_id: uuid.UUID, db: DBSession) -> ModuleResponse:
    return await ModuleService(db).get_module(project_id=project_id, module_id=module_id)


async def create_module(project_id: uuid.UUID, payload: ModuleCreate, db: DBSession) -> ModuleResponse:
    return await ModuleService(db).create_module(project_id=project_id, payload=payload)


async def update_module(project_id: uuid.UUID, module_id: uuid.UUID, payload: ModuleUpdate, db: DBSession) -> ModuleResponse:
    return await ModuleService(db).update_module(project_id=project_id, module_id=module_id, payload=payload)


async def delete_module(project_id: uuid.UUID, module_id: uuid.UUID, db: DBSession) -> Response:
    await ModuleService(db).delete_module(project_id=project_id, module_id=module_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
