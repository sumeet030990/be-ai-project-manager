import uuid
from enum import Enum

from pydantic import BaseModel, Field


class BRDSyncStatus(str, Enum):
    new = "new"
    exists = "exists"
    update = "update"


class BRDStoryResult(BaseModel):
    title: str
    description: str | None = None
    order: int
    story_points: int
    priority: int
    sync_status: BRDSyncStatus = BRDSyncStatus.new
    existing_id: str | None = None


class BRDFeatureResult(BaseModel):
    name: str
    description: str | None = None
    order: int
    priority: int
    stories: list[BRDStoryResult]
    sync_status: BRDSyncStatus = BRDSyncStatus.new
    existing_id: str | None = None


class BRDAnalysisResult(BaseModel):
    project_context: str
    features: list[BRDFeatureResult]


class BRDStorySave(BaseModel):
    title: str
    description: str | None = None
    order: int = Field(default=0, ge=0)
    story_points: int = Field(default=3, ge=1, le=5)
    priority: int = Field(default=0, ge=0)
    existing_id: str | None = None


class BRDFeatureSave(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    order: int = Field(default=0, ge=0)
    priority: int = Field(default=0, ge=0)
    stories: list[BRDStorySave] = []
    existing_id: str | None = None


class BRDBulkSaveRequest(BaseModel):
    created_by: uuid.UUID
    features: list[BRDFeatureSave]
    project_context: str | None = None
    save_context: bool = False


class BRDBulkSaveResponse(BaseModel):
    created_features: int
    updated_features: int
    created_stories: int
    updated_stories: int
