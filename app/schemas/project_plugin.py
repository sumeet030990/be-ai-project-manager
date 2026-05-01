import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Ecosystem = Literal["npm", "pip", "maven", "composer", "gem", "nuget", "cargo", "other"]


class ProjectPluginCreate(BaseModel):
    tech_stack_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    version: str | None = Field(default=None, max_length=100)
    ecosystem: Ecosystem | None = None
    description: str | None = None


class ProjectPluginUpdate(BaseModel):
    tech_stack_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    version: str | None = Field(default=None, max_length=100)
    ecosystem: Ecosystem | None = None
    description: str | None = None


class ProjectPluginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    tech_stack_id: uuid.UUID
    name: str
    version: str | None
    ecosystem: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime
