import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.repositories.module_repository import ModuleRepository
from app.repositories.story_repository import StoryRepository
from app.schemas.common import PaginatedResponse
from app.schemas.story import StoryCreate, StoryResponse, StoryUpdate, SubStoryCreate, SubStoryUpdate
from database.models.story import Story


class StoryService:
    def __init__(self, session: AsyncSession):
        self.repository = StoryRepository(session)
        self.module_repository = ModuleRepository(session)

    async def _get_module_or_404(self, module_id: uuid.UUID) -> None:
        if not await self.module_repository.get_by_id(module_id):
            raise NotFoundException("Module", str(module_id))

    async def _get_story_or_404(self, module_id: uuid.UUID, story_id: uuid.UUID) -> Story:
        story = await self.repository.get_by_module_and_id(module_id, story_id)
        if not story:
            raise NotFoundException("Story", str(story_id))
        return story

    async def _get_sub_story_or_404(self, parent_story_id: uuid.UUID, sub_story_id: uuid.UUID) -> Story:
        sub_story = await self.repository.get_sub_story_by_id(parent_story_id, sub_story_id)
        if not sub_story:
            raise NotFoundException("SubStory", str(sub_story_id))
        return sub_story

    # ── Stories ──────────────────────────────────────────────────────────────

    async def list_stories(self, module_id: uuid.UUID, page: int, size: int) -> PaginatedResponse[StoryResponse]:
        await self._get_module_or_404(module_id)
        skip = (page - 1) * size
        items, total = await self.repository.get_all_by_module(module_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[StoryResponse.model_validate(s) for s in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_story(self, module_id: uuid.UUID, story_id: uuid.UUID) -> StoryResponse:
        story = await self._get_story_or_404(module_id, story_id)
        return StoryResponse.model_validate(story)

    async def create_story(self, module_id: uuid.UUID, payload: StoryCreate) -> StoryResponse:
        await self._get_module_or_404(module_id)
        story = Story(module_id=module_id, story_type="story", **payload.model_dump())
        story = await self.repository.create(story)
        return StoryResponse.model_validate(story)

    async def update_story(self, module_id: uuid.UUID, story_id: uuid.UUID, payload: StoryUpdate) -> StoryResponse:
        story = await self._get_story_or_404(module_id, story_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(story, field, value)
        story = await self.repository.update(story)
        return StoryResponse.model_validate(story)

    async def delete_story(self, module_id: uuid.UUID, story_id: uuid.UUID) -> None:
        story = await self._get_story_or_404(module_id, story_id)
        await self.repository.delete(story)

    # ── Sub-stories ───────────────────────────────────────────────────────────

    async def list_sub_stories(self, module_id: uuid.UUID, story_id: uuid.UUID, page: int, size: int) -> PaginatedResponse[StoryResponse]:
        await self._get_story_or_404(module_id, story_id)
        skip = (page - 1) * size
        items, total = await self.repository.get_all_sub_stories(story_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[StoryResponse.model_validate(s) for s in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_sub_story(self, module_id: uuid.UUID, story_id: uuid.UUID, sub_story_id: uuid.UUID) -> StoryResponse:
        await self._get_story_or_404(module_id, story_id)
        sub_story = await self._get_sub_story_or_404(story_id, sub_story_id)
        return StoryResponse.model_validate(sub_story)

    async def create_sub_story(self, module_id: uuid.UUID, story_id: uuid.UUID, payload: SubStoryCreate) -> StoryResponse:
        await self._get_story_or_404(module_id, story_id)
        sub_story = Story(parent_story_id=story_id, story_type="sub_story", **payload.model_dump())
        sub_story = await self.repository.create(sub_story)
        return StoryResponse.model_validate(sub_story)

    async def update_sub_story(self, module_id: uuid.UUID, story_id: uuid.UUID, sub_story_id: uuid.UUID, payload: SubStoryUpdate) -> StoryResponse:
        await self._get_story_or_404(module_id, story_id)
        sub_story = await self._get_sub_story_or_404(story_id, sub_story_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(sub_story, field, value)
        sub_story = await self.repository.update(sub_story)
        return StoryResponse.model_validate(sub_story)

    async def delete_sub_story(self, module_id: uuid.UUID, story_id: uuid.UUID, sub_story_id: uuid.UUID) -> None:
        await self._get_story_or_404(module_id, story_id)
        sub_story = await self._get_sub_story_or_404(story_id, sub_story_id)
        await self.repository.delete(sub_story)
