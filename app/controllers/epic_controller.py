import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.epic import EpicCreate, EpicResponse, EpicUpdate
from app.services.epic_service import EpicService


async def list_epics(project_id: uuid.UUID, page: int, size: int, db: DBSession) -> PaginatedResponse[EpicResponse]:
    return await EpicService(db).list_epics(project_id=project_id, page=page, size=size)


async def get_epic(project_id: uuid.UUID, epic_id: uuid.UUID, db: DBSession) -> EpicResponse:
    return await EpicService(db).get_epic(project_id=project_id, epic_id=epic_id)


async def create_epic(project_id: uuid.UUID, payload: EpicCreate, db: DBSession) -> EpicResponse:
    return await EpicService(db).create_epic(project_id=project_id, payload=payload)


async def update_epic(project_id: uuid.UUID, epic_id: uuid.UUID, payload: EpicUpdate, db: DBSession) -> EpicResponse:
    return await EpicService(db).update_epic(project_id=project_id, epic_id=epic_id, payload=payload)


async def delete_epic(project_id: uuid.UUID, epic_id: uuid.UUID, db: DBSession) -> Response:
    await EpicService(db).delete_epic(project_id=project_id, epic_id=epic_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
