import uuid

from fastapi import APIRouter

from app.controllers import story_controller
from app.core.dependencies import DBSession
from app.schemas.story import JiraSyncResult, StoryResponse

router = APIRouter(tags=["JIRA"])


@router.get("/jira/issue-types")
async def list_jira_issue_types():
    return await story_controller.list_jira_issue_types()


@router.post("/modules/{module_id}/stories/{story_id}/jira/pull", response_model=StoryResponse)
async def pull_story_from_jira(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession):
    return await story_controller.pull_story_from_jira(module_id=module_id, story_id=story_id, db=db)


@router.post("/modules/{module_id}/stories/jira/sync", response_model=JiraSyncResult)
async def sync_stories_from_jira(module_id: uuid.UUID, db: DBSession):
    return await story_controller.sync_stories_to_jira(module_id=module_id, db=db)


@router.post("/modules/{module_id}/stories/{story_id}/jira", response_model=StoryResponse)
async def create_story_in_jira(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession):
    return await story_controller.create_story_in_jira(module_id=module_id, story_id=story_id, db=db)


@router.put("/modules/{module_id}/stories/{story_id}/jira", response_model=StoryResponse)
async def update_story_in_jira(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession):
    return await story_controller.update_story_in_jira(module_id=module_id, story_id=story_id, db=db)


@router.delete("/modules/{module_id}/stories/{story_id}/jira", response_model=StoryResponse)
async def delete_story_from_jira(module_id: uuid.UUID, story_id: uuid.UUID, db: DBSession):
    return await story_controller.delete_story_from_jira(module_id=module_id, story_id=story_id, db=db)
