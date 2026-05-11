import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TestCaseType = Literal["positive", "negative"]


class TestCaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    steps: str | None = None
    expected_result: str | None = None
    test_type: TestCaseType = "positive"
    order: int = Field(default=0, ge=0)


class TestCaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    steps: str | None = None
    expected_result: str | None = None
    test_type: TestCaseType | None = None
    order: int | None = Field(default=None, ge=0)


class TestCaseGenerateRequest(BaseModel):
    context: str | None = None


class TestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    story_id: uuid.UUID
    title: str
    description: str | None
    steps: str | None
    expected_result: str | None
    test_type: str
    order: int
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime
