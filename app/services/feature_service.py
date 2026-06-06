import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.repositories.feature_repository import FeatureRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.story_repository import StoryRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.feature import FeatureCreate, FeatureResponse, FeatureUpdate
from database.models.feature import Feature


class FeatureService:
    def __init__(self, session: AsyncSession):
        self.repository = FeatureRepository(session)
        self.project_repository = ProjectRepository(session)
        self.story_repository = StoryRepository(session)
        self.user_repository = UserRepository(session)

    async def list_features(self, project_id: uuid.UUID, page: int, size: int) -> PaginatedResponse[FeatureResponse]:
        if not await self.project_repository.get_by_id(project_id):
            raise NotFoundException("Project", str(project_id))
        skip = (page - 1) * size
        items, total = await self.repository.get_all_by_project(project_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[FeatureResponse.model_validate(m) for m in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_feature(self, project_id: uuid.UUID, feature_id: uuid.UUID) -> FeatureResponse:
        feature = await self.repository.get_by_project_and_id(project_id, feature_id)
        if not feature:
            raise NotFoundException("Feature", str(feature_id))
        return FeatureResponse.model_validate(feature)

    async def create_feature(self, project_id: uuid.UUID, payload: FeatureCreate) -> FeatureResponse:
        if not await self.project_repository.get_by_id(project_id):
            raise NotFoundException("Project", str(project_id))
        if not await self.user_repository.get_by_id(payload.created_by):
            raise NotFoundException("User", str(payload.created_by))
        feature = Feature(project_id=project_id, **payload.model_dump())
        feature = await self.repository.create(feature)
        return FeatureResponse.model_validate(feature)

    async def update_feature(self, project_id: uuid.UUID, feature_id: uuid.UUID, payload: FeatureUpdate) -> FeatureResponse:
        feature = await self.repository.get_by_project_and_id(project_id, feature_id)
        if not feature:
            raise NotFoundException("Feature", str(feature_id))
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(feature, field, value)
        feature = await self.repository.update(feature)
        return FeatureResponse.model_validate(feature)

    async def delete_feature(self, project_id: uuid.UUID, feature_id: uuid.UUID, delete_remote: bool = False) -> None:
        from app.services.jira_service import JiraService

        feature = await self.repository.get_by_project_and_id(project_id, feature_id)
        if not feature:
            raise NotFoundException("Feature", str(feature_id))
        if delete_remote:
            linked_stories = await self.story_repository.get_jira_linked_stories_by_feature(feature_id)
            if linked_stories:
                jira = JiraService()
                for story in linked_stories:
                    await jira.delete_issue(story.jira_issue_key)
        await self.repository.delete(feature)
