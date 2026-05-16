import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectResponse
from app.schemas.user import JiraUserPreview, JiraUserSyncRequest, JiraUserSyncResult, UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService


async def get_user(user_id: uuid.UUID, db: DBSession) -> UserResponse:
    return await UserService(db).get_user(user_id)


async def list_users(page: int, size: int, db: DBSession) -> PaginatedResponse[UserResponse]:
    return await UserService(db).list_users(page=page, size=size)


async def create_user(payload: UserCreate, db: DBSession) -> UserResponse:
    return await UserService(db).create_user(payload)


async def update_user(user_id: uuid.UUID, payload: UserUpdate, db: DBSession) -> UserResponse:
    return await UserService(db).update_user(user_id, payload)


async def list_user_projects(user_id: uuid.UUID, page: int, size: int, db: DBSession) -> PaginatedResponse[ProjectResponse]:
    return await UserService(db).list_user_projects(user_id, page=page, size=size)


async def delete_user(user_id: uuid.UUID, db: DBSession) -> Response:
    await UserService(db).delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def preview_jira_users(project_id: uuid.UUID, db: DBSession) -> list[JiraUserPreview]:
    return await UserService(db).preview_jira_users(project_id)


async def sync_users_from_jira(payload: JiraUserSyncRequest, db: DBSession) -> JiraUserSyncResult:
    return await UserService(db).sync_users_from_jira(payload)
