import uuid

from fastapi import status
from fastapi.responses import Response

from app.core.dependencies import DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.story import JiraSyncResult, StoryCreate, StoryRefineRequest, StoryResponse, StoryUpdate
from app.services.story_service import StoryService
from app.services.jira_service import JiraService


async def list_stories(module_id: uuid.UUID, page: int, size: int, db: DBSession) -> PaginatedResponse[StoryResponse]:
    return await StoryService(db).list_stories(module_id=module_id, page=page, size=size)


async def get_story(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession) -> StoryResponse:
    return await StoryService(db).get_story(module_id=module_id, story_id=story_id)


async def create_story(module_id: uuid.UUID, payload: StoryCreate, db: DBSession) -> StoryResponse:
    return await StoryService(db).create_story(module_id=module_id, payload=payload)


async def update_story(module_id: uuid.UUID, story_id: uuid.UUID, payload: StoryUpdate, db: DBSession) -> StoryResponse:
    return await StoryService(db).update_story(module_id=module_id, story_id=story_id, payload=payload)


async def delete_story(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession, delete_remote: bool = False) -> Response:
    await StoryService(db).delete_story(module_id=module_id, story_id=story_id, delete_remote=delete_remote)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def refine_story(module_id: uuid.UUID, story_id: uuid.UUID, payload: StoryRefineRequest, db: DBSession) -> StoryResponse:
    return await StoryService(db).refine_story(module_id=module_id, story_id=story_id, payload=payload)


async def generate_stories(project_id: uuid.UUID, module_id: uuid.UUID, db: DBSession, context: str | None = None) -> list[StoryResponse]:
    return await StoryService(db).generate_stories(project_id=project_id, module_id=module_id, context=context)


async def pull_story_from_jira(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession) -> StoryResponse:
    return await StoryService(db).pull_story_from_jira(module_id=module_id, story_id=story_id)


async def sync_stories_to_jira(module_id: uuid.UUID, db: DBSession) -> JiraSyncResult:
    return await StoryService(db).sync_stories_to_jira(module_id=module_id)


async def create_story_in_jira(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession) -> StoryResponse:
    return await StoryService(db).create_story_in_jira(module_id=module_id, story_id=story_id)


async def update_story_in_jira(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession) -> StoryResponse:
    return await StoryService(db).update_story_in_jira(module_id=module_id, story_id=story_id)


async def delete_story_from_jira(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession) -> StoryResponse:
    return await StoryService(db).delete_story_from_jira(module_id=module_id, story_id=story_id)


async def list_jira_issue_types(project_id: uuid.UUID, db: DBSession) -> list[dict]:
    service = StoryService(db)
    jira_project_key = await service._get_jira_project_key(project_id)
    return await JiraService().fetch_issue_types(jira_project_key)
