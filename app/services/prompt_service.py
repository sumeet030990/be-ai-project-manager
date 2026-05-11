import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.repositories.prompt_repository import PromptRepository
from app.repositories.story_repository import StoryRepository
from app.schemas.common import PaginatedResponse
from app.schemas.prompt import PromptCreate, PromptResponse
from database.models.prompt import Prompt


class PromptService:
    def __init__(self, session: AsyncSession):
        self.repository = PromptRepository(session)
        self.story_repository = StoryRepository(session)

    async def _get_story_or_404(self, module_id: uuid.UUID, story_id: uuid.UUID):
        story = await self.story_repository.get_by_module_and_id(module_id, story_id)
        if not story:
            raise NotFoundException("Story", str(story_id))
        return story

    async def list_prompts(
        self, module_id: uuid.UUID, story_id: uuid.UUID, page: int, size: int
    ) -> PaginatedResponse[PromptResponse]:
        await self._get_story_or_404(module_id, story_id)
        skip = (page - 1) * size
        items, total = await self.repository.get_all_by_story(story_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[PromptResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def save_prompt(
        self, module_id: uuid.UUID, story_id: uuid.UUID, payload: PromptCreate
    ) -> PromptResponse:
        await self._get_story_or_404(module_id, story_id)
        prompt = Prompt(story_id=story_id, **payload.model_dump())
        prompt = await self.repository.create(prompt)
        return PromptResponse.model_validate(prompt)
