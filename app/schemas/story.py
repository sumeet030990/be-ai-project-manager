import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

StoryStatus = Literal["draft", "review", "approved", "rejected", "in_progress", "done"]
StoryType = Literal["story", "sub_story"]


class StoryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    order: int = Field(default=0, ge=0)
    status: StoryStatus = "draft"


class SubStoryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    order: int = Field(default=0, ge=0)
    status: StoryStatus = "draft"
    business_rules: str | None = None
    acceptance_criteria: str | None = None
    file_references: str | None = None
    urls: str | None = None


class StoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    order: int | None = Field(default=None, ge=0)
    status: StoryStatus | None = None


class SubStoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    order: int | None = Field(default=None, ge=0)
    status: StoryStatus | None = None
    business_rules: str | None = None
    acceptance_criteria: str | None = None
    file_references: str | None = None
    urls: str | None = None


class StoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    module_id: uuid.UUID | None
    parent_story_id: uuid.UUID | None
    story_type: str
    title: str
    description: str | None
    order: int
    status: str
    is_ai_generated: bool
    azure_work_item_id: int | None
    business_rules: str | None
    acceptance_criteria: str | None
    file_references: str | None
    urls: str | None
    created_at: datetime
    updated_at: datetime
