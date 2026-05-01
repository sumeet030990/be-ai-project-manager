import uuid

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from app.controllers import story_controller
from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.story import StoryCreate, StoryResponse, StoryUpdate, SubStoryCreate, SubStoryUpdate

router = APIRouter(tags=["Stories"])


# ── Stories (under module) ────────────────────────────────────────────────────

@router.get("/modules/{module_id}/stories", response_model=PaginatedResponse[StoryResponse])
async def list_stories(
    module_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await story_controller.list_stories(module_id=module_id, page=page, size=size, db=db)


@router.get("/modules/{module_id}/stories/{story_id}", response_model=StoryResponse)
async def get_story(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession):
    return await story_controller.get_story(module_id=module_id, story_id=story_id, db=db)


@router.post("/modules/{module_id}/stories", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(module_id: uuid.UUID, payload: StoryCreate, db: DBSession):
    return await story_controller.create_story(module_id=module_id, payload=payload, db=db)


@router.patch("/modules/{module_id}/stories/{story_id}", response_model=StoryResponse)
async def update_story(module_id: uuid.UUID, story_id: uuid.UUID, payload: StoryUpdate, db: DBSession):
    return await story_controller.update_story(module_id=module_id, story_id=story_id, payload=payload, db=db)


@router.delete("/modules/{module_id}/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession) -> Response:
    return await story_controller.delete_story(module_id=module_id, story_id=story_id, db=db)


# ── Sub-stories (under story) ─────────────────────────────────────────────────

@router.get("/modules/{module_id}/stories/{story_id}/sub-stories", response_model=PaginatedResponse[StoryResponse])
async def list_sub_stories(
    module_id: uuid.UUID,
    story_id: uuid.UUID,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await story_controller.list_sub_stories(module_id=module_id, story_id=story_id, page=page, size=size, db=db)


@router.get("/modules/{module_id}/stories/{story_id}/sub-stories/{sub_story_id}", response_model=StoryResponse)
async def get_sub_story(module_id: uuid.UUID, story_id: uuid.UUID, sub_story_id: uuid.UUID, db: DBSession):
    return await story_controller.get_sub_story(module_id=module_id, story_id=story_id, sub_story_id=sub_story_id, db=db)


@router.post("/modules/{module_id}/stories/{story_id}/sub-stories", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_sub_story(module_id: uuid.UUID, story_id: uuid.UUID, payload: SubStoryCreate, db: DBSession):
    return await story_controller.create_sub_story(module_id=module_id, story_id=story_id, payload=payload, db=db)


@router.patch("/modules/{module_id}/stories/{story_id}/sub-stories/{sub_story_id}", response_model=StoryResponse)
async def update_sub_story(module_id: uuid.UUID, story_id: uuid.UUID, sub_story_id: uuid.UUID, payload: SubStoryUpdate, db: DBSession):
    return await story_controller.update_sub_story(module_id=module_id, story_id=story_id, sub_story_id=sub_story_id, payload=payload, db=db)


@router.delete("/modules/{module_id}/stories/{story_id}/sub-stories/{sub_story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sub_story(module_id: uuid.UUID, story_id: uuid.UUID, sub_story_id: uuid.UUID, db: DBSession) -> Response:
    return await story_controller.delete_sub_story(module_id=module_id, story_id=story_id, sub_story_id=sub_story_id, db=db)
