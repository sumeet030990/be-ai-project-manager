import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TechCategory = Literal["frontend", "backend", "database", "devops", "mobile", "other"]


class ProjectTechStackCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    version: str | None = Field(default=None, max_length=100)
    category: TechCategory
    description: str | None = None


class ProjectTechStackUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    version: str | None = Field(default=None, max_length=100)
    category: TechCategory | None = None
    description: str | None = None


class ProjectTechStackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    version: str | None
    category: str
    description: str | None
    created_at: datetime
    updated_at: datetime
