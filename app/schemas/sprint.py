import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.story import StoryResponse

SprintStatus = Literal["planning", "active", "completed"]


# ── CRUD schemas ──────────────────────────────────────────────────────────────

class SprintCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    goal: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class SprintUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    goal: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: SprintStatus | None = None


class SprintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    goal: str | None
    start_date: date | None
    end_date: date | None
    status: str
    jira_sprint_id: int | None
    created_at: datetime
    updated_at: datetime


# ── Story assignment ──────────────────────────────────────────────────────────

class SprintStoriesRequest(BaseModel):
    story_ids: list[uuid.UUID] = Field(..., min_length=1)


# ── Backlog view ──────────────────────────────────────────────────────────────

class BacklogFeatureGroup(BaseModel):
    feature_id: uuid.UUID
    feature_name: str
    jira_epic_key: str | None
    stories: list[StoryResponse]


class BacklogResponse(BaseModel):
    features: list[BacklogFeatureGroup]
    total_stories: int
    total_points: int


# ── Active Sprint board view ──────────────────────────────────────────────────

class SprintBoardColumns(BaseModel):
    todo: list[StoryResponse]
    in_progress: list[StoryResponse]
    in_review: list[StoryResponse]
    done: list[StoryResponse]


class ActiveSprintResponse(BaseModel):
    sprint: SprintResponse
    columns: SprintBoardColumns
    total_points: int
    completed_points: int


# ── JIRA sync ─────────────────────────────────────────────────────────────────

class SprintSyncFailure(BaseModel):
    jira_sprint_id: int
    name: str
    error: str


class SprintSyncResult(BaseModel):
    fetched: int
    created: list[SprintResponse]
    updated: list[SprintResponse]
    failed: list[SprintSyncFailure]


# ── AI planning ───────────────────────────────────────────────────────────────

class SprintAIPlanRequest(BaseModel):
    capacity: int = Field(..., ge=1, description="Sprint capacity in story points")
    context: str | None = None
    config_id: str | None = None
    feature_ids: list[uuid.UUID] | None = None


class SprintAIPlanResult(BaseModel):
    selected_stories: list[StoryResponse]
    total_points: int
    reasoning: str
