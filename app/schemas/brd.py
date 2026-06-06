import uuid

from pydantic import BaseModel, Field


class BRDSyncStatus(str):
    new = "new"
    exists = "exists"
    update = "update"


# ── Analysis result types (returned by analyze endpoint) ──────────────────────

class BRDStoryResult(BaseModel):
    title: str
    description: str | None = None
    business_rules: str | None = None
    acceptance_criteria: str | None = None
    order: int
    story_points: int
    priority: int
    sync_status: str = "new"
    existing_id: str | None = None


class BRDFeatureResult(BaseModel):
    name: str
    description: str | None = None
    business_rules: str | None = None
    acceptance_criteria: str | None = None
    order: int
    priority: int
    stories: list[BRDStoryResult]
    sync_status: str = "new"
    existing_id: str | None = None


class BRDEpicResult(BaseModel):
    name: str
    description: str | None = None
    order: int
    priority: int
    features: list[BRDFeatureResult]
    sync_status: str = "new"
    existing_id: str | None = None


class BRDAnalysisResult(BaseModel):
    project_context: str
    epics: list[BRDEpicResult]


# ── Refine schemas ─────────────────────────────────────────────────────────────

class BRDRefineRequest(BaseModel):
    item_type: str  # "epic" | "feature" | "story"
    name: str | None = None
    title: str | None = None
    description: str | None = None
    business_rules: str | None = None
    acceptance_criteria: str | None = None
    context: str | None = None
    config_id: uuid.UUID | None = None


class BRDRefineResponse(BaseModel):
    description: str | None = None
    business_rules: str | None = None
    acceptance_criteria: str | None = None


# ── Save schemas (payload for save endpoint) ───────────────────────────────────

class BRDStorySave(BaseModel):
    title: str
    description: str | None = None
    business_rules: str | None = None
    acceptance_criteria: str | None = None
    order: int = Field(default=0, ge=0)
    story_points: int = Field(default=3, ge=1, le=13)
    priority: int = Field(default=0, ge=0)
    existing_id: str | None = None


class BRDFeatureSave(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    business_rules: str | None = None
    acceptance_criteria: str | None = None
    order: int = Field(default=0, ge=0)
    priority: int = Field(default=0, ge=0)
    stories: list[BRDStorySave] = []
    existing_id: str | None = None


class BRDEpicSave(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    order: int = Field(default=0, ge=0)
    priority: int = Field(default=0, ge=0)
    features: list[BRDFeatureSave] = []
    existing_id: str | None = None


class BRDBulkSaveRequest(BaseModel):
    created_by: uuid.UUID
    epics: list[BRDEpicSave]
    project_context: str | None = None
    save_context: bool = False


class BRDBulkSaveResponse(BaseModel):
    created_epics: int
    updated_epics: int
    created_features: int
    updated_features: int
    created_stories: int
    updated_stories: int
