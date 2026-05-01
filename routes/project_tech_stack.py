import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from app.controllers import project_tech_stack_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.project_tech_stack import ProjectTechStackCreate, ProjectTechStackResponse, ProjectTechStackUpdate

router = APIRouter(prefix="/projects/{project_id}/tech-stacks", tags=["Project Tech Stacks"])


@router.get("", response_model=PaginatedResponse[ProjectTechStackResponse])
async def list_tech_stacks(
    project_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
):
    return await project_tech_stack_controller.list_tech_stacks(project_id=project_id, page=page, size=size, db=db)


@router.get("/{stack_id}", response_model=ProjectTechStackResponse)
async def get_tech_stack(project_id: uuid.UUID, stack_id: uuid.UUID, db: DBSession):
    return await project_tech_stack_controller.get_tech_stack(project_id=project_id, stack_id=stack_id, db=db)


@router.post("", response_model=ProjectTechStackResponse, status_code=status.HTTP_201_CREATED)
async def create_tech_stack(project_id: uuid.UUID, payload: ProjectTechStackCreate, db: DBSession):
    return await project_tech_stack_controller.create_tech_stack(project_id=project_id, payload=payload, db=db)


@router.patch("/{stack_id}", response_model=ProjectTechStackResponse)
async def update_tech_stack(project_id: uuid.UUID, stack_id: uuid.UUID, payload: ProjectTechStackUpdate, db: DBSession):
    return await project_tech_stack_controller.update_tech_stack(project_id=project_id, stack_id=stack_id, payload=payload, db=db)


@router.delete("/{stack_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tech_stack(project_id: uuid.UUID, stack_id: uuid.UUID, db: DBSession) -> Response:
    return await project_tech_stack_controller.delete_tech_stack(project_id=project_id, stack_id=stack_id, db=db)
