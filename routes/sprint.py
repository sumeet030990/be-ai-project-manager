import uuid

from fastapi import APIRouter, status
from fastapi.responses import Response

from app.controllers import sprint_controller
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

router = APIRouter(tags=["Sprints"])

# ── Sprint CRUD ───────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/sprints", response_model=list[SprintResponse])
async def list_sprints(project_id: uuid.UUID, db: DBSession):
    return await sprint_controller.list_sprints(project_id=project_id, db=db)


@router.post("/projects/{project_id}/sprints", response_model=SprintResponse, status_code=status.HTTP_201_CREATED)
async def create_sprint(project_id: uuid.UUID, payload: SprintCreate, db: DBSession):
    return await sprint_controller.create_sprint(project_id=project_id, payload=payload, db=db)


@router.get("/projects/{project_id}/sprints/{sprint_id}", response_model=SprintResponse)
async def get_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession):
    return await sprint_controller.get_sprint(project_id=project_id, sprint_id=sprint_id, db=db)


@router.patch("/projects/{project_id}/sprints/{sprint_id}", response_model=SprintResponse)
async def update_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintUpdate, db: DBSession):
    return await sprint_controller.update_sprint(project_id=project_id, sprint_id=sprint_id, payload=payload, db=db)


@router.delete("/projects/{project_id}/sprints/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession) -> Response:
    return await sprint_controller.delete_sprint(project_id=project_id, sprint_id=sprint_id, db=db)


# ── Sprint lifecycle ──────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/sprints/{sprint_id}/start", response_model=SprintResponse)
async def start_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession):
    return await sprint_controller.start_sprint(project_id=project_id, sprint_id=sprint_id, db=db)


@router.post("/projects/{project_id}/sprints/{sprint_id}/complete", response_model=SprintResponse)
async def complete_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession):
    return await sprint_controller.complete_sprint(project_id=project_id, sprint_id=sprint_id, db=db)


# ── Board views ───────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/sprints/board/backlog", response_model=BacklogResponse)
async def get_backlog(project_id: uuid.UUID, db: DBSession):
    return await sprint_controller.get_backlog(project_id=project_id, db=db)


@router.get("/projects/{project_id}/sprints/board/active", response_model=ActiveSprintResponse)
async def get_active_sprint_board(project_id: uuid.UUID, db: DBSession):
    return await sprint_controller.get_active_sprint_board(project_id=project_id, db=db)


# ── Story assignment ──────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/sprints/{sprint_id}/stories", response_model=list[StoryResponse])
async def get_sprint_stories(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession):
    return await sprint_controller.get_sprint_stories(project_id=project_id, sprint_id=sprint_id, db=db)


@router.post("/projects/{project_id}/sprints/{sprint_id}/stories", response_model=SprintResponse)
async def add_stories(project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintStoriesRequest, db: DBSession):
    return await sprint_controller.add_stories(project_id=project_id, sprint_id=sprint_id, payload=payload, db=db)


@router.delete("/projects/{project_id}/sprints/{sprint_id}/stories", response_model=SprintResponse)
async def remove_stories(project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintStoriesRequest, db: DBSession):
    return await sprint_controller.remove_stories(project_id=project_id, sprint_id=sprint_id, payload=payload, db=db)


# ── JIRA Sync ─────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/sprints/sync", response_model=SprintSyncResult)
async def sync_from_jira(project_id: uuid.UUID, db: DBSession):
    return await sprint_controller.sync_from_jira(project_id=project_id, db=db)


@router.post("/projects/{project_id}/sprints/{sprint_id}/push-to-jira", response_model=SprintResponse)
async def push_sprint_to_jira(project_id: uuid.UUID, sprint_id: uuid.UUID, db: DBSession):
    return await sprint_controller.push_sprint_to_jira(project_id=project_id, sprint_id=sprint_id, db=db)


# ── AI Planning ───────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/sprints/{sprint_id}/ai-plan", response_model=SprintAIPlanResult)
async def ai_plan_sprint(project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintAIPlanRequest, db: DBSession):
    return await sprint_controller.ai_plan_sprint(project_id=project_id, sprint_id=sprint_id, payload=payload, db=db)
