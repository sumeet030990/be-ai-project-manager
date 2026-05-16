import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    project_info: str | None = None
    company_id: uuid.UUID
    created_by: uuid.UUID


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    project_info: str | None = None
    status: str | None = Field(default=None, min_length=1, max_length=50)
    is_active: bool | None = None


class ProjectUserCreate(BaseModel):
    user_ids: list[uuid.UUID] = Field(..., min_length=1)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    project_info: str | None
    status: str
    is_active: bool
    company_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
