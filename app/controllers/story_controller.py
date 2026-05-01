import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.story import StoryCreate, StoryResponse, StoryUpdate, SubStoryCreate, SubStoryUpdate
from app.services.story_service import StoryService


async def list_stories(module_id: uuid.UUID, page: int, size: int, db: DBSession) -> PaginatedResponse[StoryResponse]:
    return await StoryService(db).list_stories(module_id=module_id, page=page, size=size)


async def get_story(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession) -> StoryResponse:
    return await StoryService(db).get_story(module_id=module_id, story_id=story_id)


async def create_story(module_id: uuid.UUID, payload: StoryCreate, db: DBSession) -> StoryResponse:
    return await StoryService(db).create_story(module_id=module_id, payload=payload)


async def update_story(module_id: uuid.UUID, story_id: uuid.UUID, payload: StoryUpdate, db: DBSession) -> StoryResponse:
    return await StoryService(db).update_story(module_id=module_id, story_id=story_id, payload=payload)


async def delete_story(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession) -> Response:
    await StoryService(db).delete_story(module_id=module_id, story_id=story_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def list_sub_stories(module_id: uuid.UUID, story_id: uuid.UUID, page: int, size: int, db: DBSession) -> PaginatedResponse[StoryResponse]:
    return await StoryService(db).list_sub_stories(module_id=module_id, story_id=story_id, page=page, size=size)


async def get_sub_story(module_id: uuid.UUID, story_id: uuid.UUID, sub_story_id: uuid.UUID, db: DBSession) -> StoryResponse:
    return await StoryService(db).get_sub_story(module_id=module_id, story_id=story_id, sub_story_id=sub_story_id)


async def create_sub_story(module_id: uuid.UUID, story_id: uuid.UUID, payload: SubStoryCreate, db: DBSession) -> StoryResponse:
    return await StoryService(db).create_sub_story(module_id=module_id, story_id=story_id, payload=payload)


async def update_sub_story(module_id: uuid.UUID, story_id: uuid.UUID, sub_story_id: uuid.UUID, payload: SubStoryUpdate, db: DBSession) -> StoryResponse:
    return await StoryService(db).update_sub_story(module_id=module_id, story_id=story_id, sub_story_id=sub_story_id, payload=payload)


async def delete_sub_story(module_id: uuid.UUID, story_id: uuid.UUID, sub_story_id: uuid.UUID, db: DBSession) -> Response:
    await StoryService(db).delete_sub_story(module_id=module_id, story_id=story_id, sub_story_id=sub_story_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
