import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from app.controllers import project_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectUserCreate
from app.schemas.user import UserResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    company_id: uuid.UUID | None = Query(default=None),
):
    """List projects with pagination. Can also filter projects by company if company_id is provided."""
    return await project_controller.list_projects(page=page, size=size, company_id=company_id, db=db)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: uuid.UUID, db: DBSession):
    return await project_controller.get_project(project_id=project_id, db=db)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: DBSession):
    return await project_controller.create_project(payload=payload, db=db)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: uuid.UUID, payload: ProjectUpdate, db: DBSession):
    return await project_controller.update_project(project_id=project_id, payload=payload, db=db)


@router.get("/{project_id}/users", response_model=PaginatedResponse[UserResponse])
async def list_project_users(
    project_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await project_controller.list_project_users(project_id=project_id, page=page, size=size, db=db)


@router.post("/{project_id}/users", response_model=list[UserResponse], status_code=status.HTTP_201_CREATED)
async def add_project_users(project_id: uuid.UUID, payload: ProjectUserCreate, db: DBSession):
    return await project_controller.add_project_users(project_id=project_id, payload=payload, db=db)


@router.delete("/{project_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_user(project_id: uuid.UUID, user_id: uuid.UUID, db: DBSession) -> Response:
    return await project_controller.remove_project_user(project_id=project_id, user_id=user_id, db=db)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: uuid.UUID, db: DBSession) -> Response:
    return await project_controller.delete_project(project_id=project_id, db=db)
