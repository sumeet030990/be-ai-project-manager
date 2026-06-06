import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FeatureStatus = Literal["draft", "ready", "in_progress", "done"]


class FeatureCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    order: int = Field(default=0, ge=0)
    status: FeatureStatus = "draft"
    priority: int = Field(default=0, ge=0)
    created_by: uuid.UUID


class FeatureUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    order: int | None = Field(default=None, ge=0)
    status: FeatureStatus | None = None
    priority: int | None = Field(default=None, ge=0)
    business_rules: str | None = None
    acceptance_criteria: str | None = None


class FeatureGenerateRequest(BaseModel):
    context: str | None = None
    config_id: str | None = None


class FeatureRefineRequest(BaseModel):
    context: str | None = None
    config_id: str | None = None


class FeatureRefineResponse(BaseModel):
    description: str
    business_rules: str
    acceptance_criteria: str


class FeatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    epic_id: uuid.UUID
    created_by: uuid.UUID
    name: str
    description: str | None
    order: int
    status: str
    priority: int
    is_ai_generated: bool
    business_rules: str | None
    acceptance_criteria: str | None
    created_at: datetime
    updated_at: datetime
