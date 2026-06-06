import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from app.controllers import story_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.story import StoryCreate, StoryGenerateRequest, StoryRefineRequest, StoryResponse, StoryUpdate

router = APIRouter(tags=["Stories"])


@router.get("/features/{feature_id}/stories", response_model=PaginatedResponse[StoryResponse])
async def list_stories(
    feature_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await story_controller.list_stories(feature_id=feature_id, page=page, size=size, db=db)


@router.get("/features/{feature_id}/stories/{story_id}", response_model=StoryResponse)
async def get_story(feature_id: uuid.UUID, story_id: uuid.UUID, db: DBSession):
    return await story_controller.get_story(feature_id=feature_id, story_id=story_id, db=db)


@router.post("/features/{feature_id}/stories", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(feature_id: uuid.UUID, payload: StoryCreate, db: DBSession):
    return await story_controller.create_story(feature_id=feature_id, payload=payload, db=db)


@router.patch("/features/{feature_id}/stories/{story_id}", response_model=StoryResponse)
async def update_story(feature_id: uuid.UUID, story_id: uuid.UUID, payload: StoryUpdate, db: DBSession):
    return await story_controller.update_story(feature_id=feature_id, story_id=story_id, payload=payload, db=db)


@router.post("/features/{feature_id}/stories/{story_id}/refine", response_model=StoryResponse)
async def refine_story(feature_id: uuid.UUID, story_id: uuid.UUID, payload: StoryRefineRequest, db: DBSession):
    return await story_controller.refine_story(feature_id=feature_id, story_id=story_id, payload=payload, db=db)


@router.delete("/features/{feature_id}/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    feature_id: uuid.UUID,
    story_id: uuid.UUID,
    db: DBSession,
    delete_remote: bool = Query(default=False),
) -> Response:
    return await story_controller.delete_story(feature_id=feature_id, story_id=story_id, db=db, delete_remote=delete_remote)


@router.post(
    "/features/{feature_id}/generate-stories",
    response_model=list[StoryResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_stories(feature_id: uuid.UUID, db: DBSession, payload: StoryGenerateRequest | None = None):
    return await story_controller.generate_stories(
        feature_id=feature_id,
        db=db,
        context=payload.context if payload else None,
        config_id=payload.config_id if payload else None,
    )
