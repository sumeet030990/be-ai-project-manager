import uuid

from fastapi import APIRouter

from app.controllers import story_controller, user_controller
from app.core.dependencies import DBSession
from app.schemas.story import JiraSyncResult, StoryResponse
from app.schemas.user import JiraUserPreview, JiraUserSyncRequest, JiraUserSyncResult

router = APIRouter(tags=["JIRA"])


@router.get("/jira/users/preview", response_model=list[JiraUserPreview])
async def preview_jira_users(project_id: uuid.UUID, db: DBSession):
    return await user_controller.preview_jira_users(project_id=project_id, db=db)


@router.post("/jira/users/sync", response_model=JiraUserSyncResult)
async def sync_users_from_jira(payload: JiraUserSyncRequest, db: DBSession):
    return await user_controller.sync_users_from_jira(payload=payload, db=db)


@router.get("/jira/issue-types")
async def list_jira_issue_types(project_id: uuid.UUID, db: DBSession):
    return await story_controller.list_jira_issue_types(project_id=project_id, db=db)


@router.post("/features/{feature_id}/stories/{story_id}/jira/pull", response_model=StoryResponse)
async def pull_story_from_jira(feature_id: uuid.UUID, story_id: uuid.UUID, db: DBSession):
    return await story_controller.pull_story_from_jira(feature_id=feature_id, story_id=story_id, db=db)


@router.post("/features/{feature_id}/stories/jira/sync", response_model=JiraSyncResult)
async def sync_stories_from_jira(feature_id: uuid.UUID, db: DBSession):
    return await story_controller.sync_stories_to_jira(feature_id=feature_id, db=db)


@router.post("/features/{feature_id}/stories/{story_id}/jira", response_model=StoryResponse)
async def create_story_in_jira(feature_id: uuid.UUID, story_id: uuid.UUID, db: DBSession):
    return await story_controller.create_story_in_jira(feature_id=feature_id, story_id=story_id, db=db)


@router.put("/features/{feature_id}/stories/{story_id}/jira", response_model=StoryResponse)
async def update_story_in_jira(feature_id: uuid.UUID, story_id: uuid.UUID, db: DBSession):
    return await story_controller.update_story_in_jira(feature_id=feature_id, story_id=story_id, db=db)


@router.delete("/features/{feature_id}/stories/{story_id}/jira", response_model=StoryResponse)
async def delete_story_from_jira(feature_id: uuid.UUID, story_id: uuid.UUID, db: DBSession):
    return await story_controller.delete_story_from_jira(feature_id=feature_id, story_id=story_id, db=db)
