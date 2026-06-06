import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from app.controllers import epic_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.epic import EpicCreate, EpicResponse, EpicUpdate

router = APIRouter(prefix="/projects/{project_id}/epics", tags=["Epics"])


@router.get("", response_model=PaginatedResponse[EpicResponse])
async def list_epics(
    project_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await epic_controller.list_epics(project_id=project_id, page=page, size=size, db=db)


@router.get("/{epic_id}", response_model=EpicResponse)
async def get_epic(project_id: uuid.UUID, epic_id: uuid.UUID, db: DBSession):
    return await epic_controller.get_epic(project_id=project_id, epic_id=epic_id, db=db)


@router.post("", response_model=EpicResponse, status_code=status.HTTP_201_CREATED)
async def create_epic(project_id: uuid.UUID, payload: EpicCreate, db: DBSession):
    return await epic_controller.create_epic(project_id=project_id, payload=payload, db=db)


@router.patch("/{epic_id}", response_model=EpicResponse)
async def update_epic(project_id: uuid.UUID, epic_id: uuid.UUID, payload: EpicUpdate, db: DBSession):
    return await epic_controller.update_epic(project_id=project_id, epic_id=epic_id, payload=payload, db=db)


@router.delete("/{epic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_epic(project_id: uuid.UUID, epic_id: uuid.UUID, db: DBSession) -> Response:
    return await epic_controller.delete_epic(project_id=project_id, epic_id=epic_id, db=db)
