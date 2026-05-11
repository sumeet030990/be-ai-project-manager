import json
import math
import re
import uuid
from typing import Any

from groq import BadRequestError as GroqBadRequestError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_client import get_ai_client
from app.core.exceptions import NotFoundException, ServiceUnavailableException
from app.repositories.module_repository import ModuleRepository
from app.repositories.story_repository import StoryRepository
from app.repositories.test_case_repository import TestCaseRepository
from app.schemas.common import PaginatedResponse
from app.schemas.test_case import TestCaseCreate, TestCaseGenerateRequest, TestCaseResponse, TestCaseUpdate
from database.models.test_case import TestCase

_GROQ_MODEL = "llama-3.3-70b-versatile"

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


async def _call_generate_test_cases_ai(story_context: str, manager_note: str) -> list[dict]:
    """
    Call Groq with tool-calling to generate test cases.
    Handles the case where llama-3.3-70b falls back to a tag-based XML format
    (<function=save_test_cases>[...]</function>) instead of standard JSON tool calls.
    """
    try:
        response = await get_ai_client().chat.completions.create(
            model=_GROQ_MODEL,
            max_tokens=4096,
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
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            raise ServiceUnavailableException("AI did not return a structured response. Please try again.")
        return json.loads(tool_calls[0].function.arguments)["test_cases"]

    except GroqBadRequestError as exc:
        # llama-3.3-70b sometimes emits <function=name>[...]</function> instead of JSON tool calls.
        # Parse the failed_generation field to recover the generated test cases.
        try:
            body = exc.response.json()
            failed_gen: str = body.get("error", {}).get("failed_generation", "")
            match = re.search(r"<function=\w+>(.*?)</function>", failed_gen, re.DOTALL)
            if not match:
                raise ServiceUnavailableException("AI generation failed. Please try again.")
            return json.loads(match.group(1))
        except (ValueError, AttributeError):
            raise ServiceUnavailableException("AI generation failed. Please try again.")


class TestCaseService:
    def __init__(self, session: AsyncSession):
        self.repository = TestCaseRepository(session)
        self.story_repository = StoryRepository(session)
        self.module_repository = ModuleRepository(session)

    async def _get_story_or_404(self, module_id: uuid.UUID, story_id: uuid.UUID):
        story = await self.story_repository.get_by_module_and_id(module_id, story_id)
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
        self, module_id: uuid.UUID, story_id: uuid.UUID, page: int, size: int
    ) -> PaginatedResponse[TestCaseResponse]:
        await self._get_story_or_404(module_id, story_id)
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
        self, module_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID
    ) -> TestCaseResponse:
        await self._get_story_or_404(module_id, story_id)
        tc = await self._get_test_case_or_404(story_id, test_case_id)
        return TestCaseResponse.model_validate(tc)

    async def create_test_case(
        self, module_id: uuid.UUID, story_id: uuid.UUID, payload: TestCaseCreate
    ) -> TestCaseResponse:
        await self._get_story_or_404(module_id, story_id)
        tc = TestCase(story_id=story_id, **payload.model_dump())
        tc = await self.repository.create(tc)
        return TestCaseResponse.model_validate(tc)

    async def update_test_case(
        self, module_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID, payload: TestCaseUpdate
    ) -> TestCaseResponse:
        await self._get_story_or_404(module_id, story_id)
        tc = await self._get_test_case_or_404(story_id, test_case_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(tc, field, value)
        tc = await self.repository.update(tc)
        return TestCaseResponse.model_validate(tc)

    async def delete_test_case(
        self, module_id: uuid.UUID, story_id: uuid.UUID, test_case_id: uuid.UUID
    ) -> None:
        await self._get_story_or_404(module_id, story_id)
        tc = await self._get_test_case_or_404(story_id, test_case_id)
        await self.repository.delete(tc)

    # ── AI Generation ─────────────────────────────────────────────────────────

    async def generate_test_cases(
        self, module_id: uuid.UUID, story_id: uuid.UUID, payload: TestCaseGenerateRequest
    ) -> list[TestCaseResponse]:
        story = await self._get_story_or_404(module_id, story_id)

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

        raw: list[dict] = await _call_generate_test_cases_ai(story_context, manager_note)

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
