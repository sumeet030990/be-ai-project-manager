import uuid

from fastapi import APIRouter, Query

from app.controllers import prompt_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.prompt import PromptCreate, PromptResponse

router = APIRouter(tags=["Prompts"])

_PREFIX = "/features/{feature_id}/stories/{story_id}/prompts"


@router.get(_PREFIX, response_model=PaginatedResponse[PromptResponse])
async def list_prompts(
    feature_id: uuid.UUID,
    story_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await prompt_controller.list_prompts(
        feature_id=feature_id, story_id=story_id, page=page, size=size, db=db
    )


@router.post(_PREFIX, response_model=PromptResponse, status_code=201)
async def save_prompt(
    feature_id: uuid.UUID, story_id: uuid.UUID, payload: PromptCreate, db: DBSession
):
    return await prompt_controller.save_prompt(
        feature_id=feature_id, story_id=story_id, payload=payload, db=db
    )
