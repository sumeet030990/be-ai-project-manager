import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PromptCreate(BaseModel):
    content: str = Field(..., min_length=1)
    target_ai: str = Field(default="general", max_length=50)
    tech_stacks: str | None = None
    extra_context: str | None = None


class PromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    story_id: uuid.UUID
    content: str
    target_ai: str
    tech_stacks: str | None
    extra_context: str | None
    created_at: datetime
    updated_at: datetime
