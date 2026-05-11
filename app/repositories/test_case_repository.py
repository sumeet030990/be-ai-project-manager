import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from database.models.test_case import TestCase


class TestCaseRepository(BaseRepository[TestCase]):
    model = TestCase

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all_by_story(self, story_id: uuid.UUID, skip: int, limit: int) -> tuple[list[TestCase], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(TestCase).where(TestCase.story_id == story_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(TestCase)
            .where(TestCase.story_id == story_id)
            .order_by(TestCase.order)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_story_and_id(self, story_id: uuid.UUID, test_case_id: uuid.UUID) -> TestCase | None:
        result = await self.session.execute(
            select(TestCase).where(TestCase.story_id == story_id, TestCase.id == test_case_id)
        )
        return result.scalar_one_or_none()

    async def bulk_create(self, test_cases: list[TestCase]) -> list[TestCase]:
        self.session.add_all(test_cases)
        await self.session.flush()
        for tc in test_cases:
            await self.session.refresh(tc)
        return test_cases
