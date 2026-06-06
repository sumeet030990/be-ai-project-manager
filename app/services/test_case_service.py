import math
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_client import get_project_ai_client
from app.core.exceptions import NotFoundException
from app.repositories.feature_repository import FeatureRepository
from app.repositories.story_repository import StoryRepository
from app.repositories.test_case_repository import TestCaseRepository
from app.schemas.common import PaginatedResponse
from app.schemas.test_case import TestCaseCreate, TestCaseGenerateRequest, TestCaseResponse, TestCaseUpdate
from database.models.test_case import TestCase

_GENERATE_TEST_CASES_TOOL: Any = {
    "type": "function",
    "function": {
        "name": "save_test_cases",
        "description": "Save the generated test cases for the story.",
        "parameters": {
            "type": "object",
            "properties": {
                "test_cases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Concise test case title prefixed with [Positive] or [Negative].",
                            },
                            "description": {
                                "type": "string",
                                "description": "Context and preconditions required before executing the test.",
                            },
                            "steps": {
                                "type": "string",
                                "description": "Numbered step-by-step instructions to execute the test.",
                            },
                            "expected_result": {
                                "type": "string",
                                "description": "The exact outcome that should occur after executing the steps.",
                            },
                            "test_type": {
                                "type": "string",
                                "enum": ["positive", "negative"],
                                "description": "positive = happy path / valid input; negative = error path / invalid input / edge case.",
                            },
                            "order": {"type": "integer"},
                        },
                        "required": ["title", "description", "steps", "expected_result", "test_type", "order"],
                    },
                }
            },
            "required": ["test_cases"],
        },
    },
}




class TestCaseService:
    def __init__(self, session: AsyncSession):
        self.repository = TestCaseRepository(session)
        self.story_repository = StoryRepository(session)
        self.feature_repository = FeatureRepository(session)

    async def _get_story_or_404(self, feature_id: uuid.UUID, story_id: uuid.UUID):
        story = await self.story_repository.get_by_feature_and_id(feature_id, story_id)
        if not story:
            raise NotFoundException("Story", str(story_id))
        return story

    async def _get_test_case_or_404(self, story_id: uuid.UUID, test_case_id: uuid.UUID) -> TestCase:
        tc = await self.repository.get_by_story_and_id(story_id, test_case_id)
        if not tc:
            raise NotFoundException("TestCase", str(test_case_id))
        return tc

    # ── CRUD ─────────────────────────────────────────────────────────────────

    async def list_test_cases(
        self, feature_id: uuid.UUID, story_id: uuid.UUID, page: int, size: int
    ) -> PaginatedResponse[TestCaseResponse]:
        await self._get_story_or_404(feature_id, story_id)
        skip = (page - 1) * size
        items, total = await self.repository.get_all_by_story(story_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[TestCaseResponse.model_validate(tc) for tc in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_test_case(
        self, feature_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID
    ) -> TestCaseResponse:
        await self._get_story_or_404(feature_id, story_id)
        tc = await self._get_test_case_or_404(story_id, test_case_id)
        return TestCaseResponse.model_validate(tc)

    async def create_test_case(
        self, feature_id: uuid.UUID, story_id: uuid.UUID, payload: TestCaseCreate
    ) -> TestCaseResponse:
        await self._get_story_or_404(feature_id, story_id)
        tc = TestCase(story_id=story_id, **payload.model_dump())
        tc = await self.repository.create(tc)
        return TestCaseResponse.model_validate(tc)

    async def update_test_case(
        self, feature_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID, payload: TestCaseUpdate
    ) -> TestCaseResponse:
        await self._get_story_or_404(feature_id, story_id)
        tc = await self._get_test_case_or_404(story_id, test_case_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(tc, field, value)
        tc = await self.repository.update(tc)
        return TestCaseResponse.model_validate(tc)

    async def delete_test_case(
        self, feature_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID
    ) -> None:
        await self._get_story_or_404(feature_id, story_id)
        tc = await self._get_test_case_or_404(story_id, test_case_id)
        await self.repository.delete(tc)

    # ── AI Generation ─────────────────────────────────────────────────────────

    async def generate_test_cases(
        self, feature_id: uuid.UUID, story_id: uuid.UUID, payload: TestCaseGenerateRequest
    ) -> list[TestCaseResponse]:
        story = await self._get_story_or_404(feature_id, story_id)
        feature = await self.feature_repository.get_by_id(feature_id)

        story_context = (
            f"Story: {story.title}\n"
            f"Description: {story.description or 'No description provided.'}\n"
            f"Business rules: {story.business_rules or 'Not defined.'}\n"
            f"Acceptance criteria: {story.acceptance_criteria or 'Not defined.'}\n"
            f"File references: {story.file_references or 'Not defined.'}\n"
            f"URLs: {story.urls or 'Not defined.'}\n"
        )

        manager_note = (
            f"Additional context from manager: {payload.context}\n\n"
            if payload.context
            else ""
        )

        config_id = uuid.UUID(payload.config_id) if payload.config_id else None
        ai_client = await get_project_ai_client(feature.project_id, self.feature_repository.session, config_id=config_id)
        result = await ai_client.chat_with_tools(
            tools=[_GENERATE_TEST_CASES_TOOL],
            tool_choice={"type": "function", "function": {"name": "save_test_cases"}},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior QA engineer who writes thorough, precise test cases. "
                        "For every story you receive, generate a balanced set of positive (happy path) "
                        "and negative (error path, edge case, invalid input) test cases. "
                        "Each test case must have clear numbered steps and a concrete expected result. "
                        "Positive tests verify the feature works as expected with valid inputs. "
                        "Negative tests verify the system handles invalid inputs, missing data, "
                        "boundary conditions, and error states gracefully."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{story_context}\n"
                        f"{manager_note}"
                        "Generate comprehensive test cases covering:\n"
                        "- All acceptance criteria (positive scenarios)\n"
                        "- Business rule violations (negative scenarios)\n"
                        "- Boundary / edge cases (negative scenarios)\n"
                        "- Missing or invalid input handling (negative scenarios)\n"
                        "Order positive tests before negative tests. "
                        "Aim for at least 3 positive and 3 negative test cases."
                    ),
                },
            ],
        )
        raw: list[dict] = result.arguments["test_cases"]

        test_cases = await self.repository.bulk_create([
            TestCase(
                story_id=story_id,
                title=tc["title"],
                description=tc.get("description"),
                steps=tc.get("steps"),
                expected_result=tc.get("expected_result"),
                test_type=tc.get("test_type", "positive"),
                order=tc.get("order", i),
                is_ai_generated=True,
            )
            for i, tc in enumerate(raw)
        ])
        return [TestCaseResponse.model_validate(tc) for tc in test_cases]
