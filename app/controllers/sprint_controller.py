import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.sprint import (
    ActiveSprintResponse,
    BacklogResponse,
    SprintAIPlanRequest,
    SprintAIPlanResult,
    SprintCreate,
    SprintResponse,
    SprintStoriesRequest,
    SprintSyncResult,
    SprintUpdate,
)
from app.schemas.story import StoryResponse
from app.services.sprint_service import SprintService


async def list_sprints(project_id: uuid.UUID, db: DBSession) -> list[SprintResponse]:
    return await SprintService(db).list_sprints(project_id=project_id)


async def get_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession) -> SprintResponse:
    return await SprintService(db).get_sprint(project_id=project_id, sprint_id=sprint_id)


async def create_sprint(project_id: uuid.UUID, payload: SprintCreate, db: DBSession) -> SprintResponse:
    return await SprintService(db).create_sprint(project_id=project_id, payload=payload)


async def update_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintUpdate, db: DBSession) -> SprintResponse:
    return await SprintService(db).update_sprint(project_id=project_id, sprint_id=sprint_id, payload=payload)


async def delete_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession) -> Response:
    await SprintService(db).delete_sprint(project_id=project_id, sprint_id=sprint_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def start_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession) -> SprintResponse:
    return await SprintService(db).start_sprint(project_id=project_id, sprint_id=sprint_id)


async def complete_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession) -> SprintResponse:
    return await SprintService(db).complete_sprint(project_id=project_id, sprint_id=sprint_id)


async def get_backlog(project_id: uuid.UUID, db: DBSession) -> BacklogResponse:
    return await SprintService(db).get_backlog(project_id=project_id)


async def get_active_sprint_board(project_id: uuid.UUID, db: DBSession) -> ActiveSprintResponse:
    return await SprintService(db).get_active_sprint_board(project_id=project_id)


async def add_stories(project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintStoriesRequest, db: DBSession) -> SprintResponse:
    return await SprintService(db).add_stories(project_id=project_id, sprint_id=sprint_id, payload=payload)


async def remove_stories(project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintStoriesRequest, db: DBSession) -> SprintResponse:
    return await SprintService(db).remove_stories(project_id=project_id, sprint_id=sprint_id, payload=payload)


async def get_sprint_stories(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession) -> list[StoryResponse]:
    return await SprintService(db).get_sprint_stories(project_id=project_id, sprint_id=sprint_id)


async def sync_from_jira(project_id: uuid.UUID, db: DBSession) -> SprintSyncResult:
    return await SprintService(db).sync_from_jira(project_id=project_id)


async def push_sprint_to_jira(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession) -> SprintResponse:
    return await SprintService(db).push_sprint_to_jira(project_id=project_id, sprint_id=sprint_id)


async def ai_plan_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintAIPlanRequest, db: DBSession) -> SprintAIPlanResult:
    return await SprintService(db).ai_plan_sprint(project_id=project_id, sprint_id=sprint_id, payload=payload)
