import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.project_tech_stack import ProjectTechStackCreate, ProjectTechStackResponse, ProjectTechStackUpdate
from app.services.project_tech_stack_service import ProjectTechStackService


async def list_tech_stacks(project_id: uuid.UUID, page: int, size: int, db: DBSession) -> PaginatedResponse[ProjectTechStackResponse]:
    return await ProjectTechStackService(db).list_tech_stacks(project_id=project_id, page=page, size=size)


async def get_tech_stack(project_id: uuid.UUID, stack_id: uuid.UUID, db: DBSession) -> ProjectTechStackResponse:
    return await ProjectTechStackService(db).get_tech_stack(project_id=project_id, stack_id=stack_id)


async def create_tech_stack(project_id: uuid.UUID, payload: ProjectTechStackCreate, db: DBSession) -> ProjectTechStackResponse:
    return await ProjectTechStackService(db).create_tech_stack(project_id=project_id, payload=payload)


async def update_tech_stack(project_id: uuid.UUID, stack_id: uuid.UUID, payload: ProjectTechStackUpdate, db: DBSession) -> ProjectTechStackResponse:
    return await ProjectTechStackService(db).update_tech_stack(project_id=project_id, stack_id=stack_id, payload=payload)


async def delete_tech_stack(project_id: uuid.UUID, stack_id: uuid.UUID, db: DBSession) -> Response:
    await ProjectTechStackService(db).delete_tech_stack(project_id=project_id, stack_id=stack_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
