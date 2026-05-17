import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AIProvider = Literal["claude", "openai", "groq", "deepseek", "other"]


class ProjectAIConfigCreate(BaseModel):
    provider: AIProvider
    api_key: str = Field(..., min_length=1, description="Plaintext API key — will be encrypted at rest.")
    model_name: str = Field(..., min_length=1, max_length=200)
    is_default: bool = False


class ProjectAIConfigUpdate(BaseModel):
    provider: AIProvider | None = None
    api_key: str | None = Field(default=None, min_length=1, description="Provide only to rotate the key.")
    model_name: str | None = Field(default=None, min_length=1, max_length=200)
    is_default: bool | None = None


class ProjectAIConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: uuid.UUID
    project_id: uuid.UUID
    provider: str
    api_key_masked: str
    model_name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
