import uuid
from typing import Optional

from fastapi import status  # type: ignore
from fastapi.responses import Response # type: ignore

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectUserCreate
from app.schemas.user import UserResponse
from app.services.project_service import ProjectService


async def list_projects(page: int, size: int, company_id: uuid.UUID | None, db: DBSession) -> PaginatedResponse[ProjectResponse]:
    return await ProjectService(db).list_projects(page=page, size=size, company_id=company_id)


async def get_project(project_id: uuid.UUID, db: DBSession) -> ProjectResponse:
    return await ProjectService(db).get_project(project_id)


async def create_project(payload: ProjectCreate, db: DBSession) -> ProjectResponse:
    return await ProjectService(db).create_project(payload)


async def update_project(project_id: uuid.UUID, payload: ProjectUpdate, db: DBSession) -> ProjectResponse:
    return await ProjectService(db).update_project(project_id, payload)


async def list_project_users(project_id: uuid.UUID, page: int, size: int, db: DBSession) -> PaginatedResponse[UserResponse]:
    return await ProjectService(db).list_project_users(project_id, page=page, size=size)


async def add_project_users(project_id: uuid.UUID, payload: ProjectUserCreate, db: DBSession) -> list[UserResponse]:
    return await ProjectService(db).add_project_users(project_id, payload)


async def remove_project_user(project_id: uuid.UUID, user_id: uuid.UUID, db: DBSession) -> Response:
    await ProjectService(db).remove_project_user(project_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def delete_project(project_id: uuid.UUID, db: DBSession) -> Response:
    await ProjectService(db).delete_project(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
