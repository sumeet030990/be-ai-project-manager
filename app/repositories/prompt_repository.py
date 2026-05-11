import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from database.models.prompt import Prompt


class PromptRepository(BaseRepository[Prompt]):
    model = Prompt

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all_by_story(
        self, story_id: uuid.UUID, skip: int, limit: int
    ) -> tuple[list[Prompt], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(Prompt).where(Prompt.story_id == story_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Prompt)
            .where(Prompt.story_id == story_id)
            .order_by(Prompt.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total
