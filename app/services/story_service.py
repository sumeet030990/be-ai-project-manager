import json
import math
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_client import get_ai_client
from app.core.exceptions import NotFoundException, ServiceUnavailableException
from app.repositories.module_repository import ModuleRepository
from app.repositories.project_plugin_repository import ProjectPluginRepository
from app.repositories.project_tech_stack_repository import ProjectTechStackRepository
from app.repositories.story_repository import StoryRepository
from app.schemas.common import PaginatedResponse
from app.schemas.story import StoryCreate, StoryRefineRequest, StoryRefineResponse, StoryResponse, StoryUpdate
from database.models.story import Story

_GROQ_MODEL = "llama-3.3-70b-versatile"

_GENERATE_STORIES_TOOL: Any = {
    "type": "function",
    "function": {
        "name": "save_stories",
        "description": "Save the generated stories for the module.",
        "parameters": {
            "type": "object",
            "properties": {
                "stories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Story title prefixed with a type tag such as [FE], [BE], [API], [DB], [Infra], or [Test] based on the nature of the work."},
                            "description": {"type": "string"},
                            "order": {"type": "integer"},
                            "story_points": {
                                "type": "integer",
                                "description": "Effort estimate using Fibonacci story points. Target 3 for most stories; use 5 only when the scope is clearly larger. Never exceed 5.",
                                "minimum": 1,
                                "maximum": 5,
                            },
                        },
                        "required": ["title", "description", "order", "story_points"],
                    },
                }
            },
            "required": ["stories"],
        },
    },
}


_REFINE_STORY_TOOL: Any = {
    "type": "function",
    "function": {
        "name": "refine_story",
        "description": "Save the refined story details.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Detailed technical explanation of what needs to be implemented and why.",
                },
                "business_rules": {
                    "type": "string",
                    "description": "Business logic, constraints, and rules the implementation must follow.",
                },
                "acceptance_criteria": {
                    "type": "string",
                    "description": "Clear, testable conditions that must be met for this story to be considered done.",
                },
                "file_references": {
                    "type": "string",
                    "description": "Relevant files, directories, or modules in the codebase to look at or modify.",
                },
                "urls": {
                    "type": "string",
                    "description": "Relevant API routes, endpoints, or external documentation URLs.",
                },
            },
            "required": ["description", "business_rules", "acceptance_criteria", "file_references", "urls"],
        },
    },
}


def _build_tech_context(tech_stacks: list, plugins: list) -> str:
    if not tech_stacks:
        return "No tech stack defined for this project."
    lines = []
    plugins_by_stack: dict[str, list] = {}
    for p in plugins:
        plugins_by_stack.setdefault(str(p.tech_stack_id), []).append(p)
    for ts in tech_stacks:
        line = f"- {ts.name} {ts.version or ''} ({ts.category})".strip()
        stack_plugins = plugins_by_stack.get(str(ts.id), [])
        if stack_plugins:
            plugin_list = ", ".join(f"{p.name} {p.version or ''}".strip() for p in stack_plugins)
            line += f": {plugin_list}"
        lines.append(line)
    return "\n".join(lines)


class StoryService:
    def __init__(self, session: AsyncSession):
        self.repository = StoryRepository(session)
        self.module_repository = ModuleRepository(session)
        self.tech_stack_repository = ProjectTechStackRepository(session)
        self.plugin_repository = ProjectPluginRepository(session)

    async def _get_module_or_404(self, module_id: uuid.UUID):
        module = await self.module_repository.get_by_id(module_id)
        if not module:
            raise NotFoundException("Module", str(module_id))
        return module

    async def _get_story_or_404(self, module_id: uuid.UUID, story_id: uuid.UUID) -> Story:
        story = await self.repository.get_by_module_and_id(module_id, story_id)
        if not story:
            raise NotFoundException("Story", str(story_id))
        return story

    # ── CRUD ─────────────────────────────────────────────────────────────────

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
        story = Story(module_id=module_id, **payload.model_dump())
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

    async def refine_story(self, module_id: uuid.UUID, story_id: uuid.UUID, payload: StoryRefineRequest) -> StoryResponse:
        story = await self._get_story_or_404(module_id, story_id)
        module = await self._get_module_or_404(module_id)

        tech_stacks, _ = await self.tech_stack_repository.get_all_by_project(module.project_id, skip=0, limit=500)
        plugins, _ = await self.plugin_repository.get_all_by_project(module.project_id, skip=0, limit=500)
        tech_context = _build_tech_context(tech_stacks, plugins)

        is_refinement = any([
            story.description, story.business_rules,
            story.acceptance_criteria, story.file_references, story.urls,
        ])

        if is_refinement:
            current_state = (
                f"Current story details (already refined — update based on the manager's instructions):\n"
                f"Description: {story.description or '-'}\n"
                f"Business rules: {story.business_rules or '-'}\n"
                f"Acceptance criteria: {story.acceptance_criteria or '-'}\n"
                f"File references: {story.file_references or '-'}\n"
                f"URLs: {story.urls or '-'}\n\n"
            )
        else:
            current_state = ""

        manager_note = (
            f"Manager's instructions: {payload.context}\n\n"
            if payload.context else
            "No additional instructions — generate full details from scratch.\n\n"
        )

        response = await get_ai_client().chat.completions.create(
            model=_GROQ_MODEL,
            max_tokens=4096,
            tools=[_REFINE_STORY_TOOL],
            tool_choice={"type": "function", "function": {"name": "refine_story"}},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software architect and project manager. "
                        "You enrich user stories with detailed technical information to help developers implement them precisely.\n\n"
                        f"Project tech stack:\n{tech_context}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Module: {module.name}\n"
                        f"Module description: {module.description or 'No description provided.'}\n\n"
                        f"Story: {story.title}\n"
                        f"Story description: {story.description or 'No description provided.'}\n\n"
                        f"{current_state}"
                        f"{manager_note}"
                        "Provide:\n"
                        "- A detailed technical description of what needs to be implemented\n"
                        "- Business rules and constraints\n"
                        "- Clear, testable acceptance criteria\n"
                        "- Relevant files or directories in the codebase to reference or modify\n"
                        "- Relevant API routes, endpoints, or documentation URLs"
                    ),
                },
            ],
        )

        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            raise ServiceUnavailableException("AI did not return a structured response. Please try again.")

        refined = StoryRefineResponse(**json.loads(tool_calls[0].function.arguments))
        for field, value in refined.model_dump().items():
            setattr(story, field, value)
        story = await self.repository.update(story)
        return StoryResponse.model_validate(story)

    # ── AI Generation ─────────────────────────────────────────────────────────

    async def generate_stories(self, project_id: uuid.UUID, module_id: uuid.UUID, context: str | None = None) -> list[StoryResponse]:
        module = await self.module_repository.get_by_project_and_id(project_id, module_id)
        if not module:
            raise NotFoundException("Module", str(module_id))

        tech_stacks, _ = await self.tech_stack_repository.get_all_by_project(project_id, skip=0, limit=500)
        plugins, _ = await self.plugin_repository.get_all_by_project(project_id, skip=0, limit=500)
        tech_context = _build_tech_context(tech_stacks, plugins)

        response = await get_ai_client().chat.completions.create(
            model=_GROQ_MODEL,
            max_tokens=4096,
            tools=[_GENERATE_STORIES_TOOL],
            tool_choice={"type": "function", "function": {"name": "save_stories"}},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software project manager who breaks down technical modules "
                        "into clear, well-scoped user stories for development teams.\n\n"
                        f"Project tech stack:\n{tech_context}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Break down the following module into stories.\n\n"
                        f"Module: {module.name}\n"
                        f"Description: {module.description or 'No description provided.'}\n\n"
                        + (f"Additional context:\n{context}\n\n" if context else "")
                        + "Rules:\n"
                        "- Each story should be implementable in 1-3 days\n"
                        "- Title must start with a type tag in square brackets based on the work area:\n"
                        "  [FE] Frontend (UI, components, pages)\n"
                        "  [BE] Backend (business logic, services, controllers)\n"
                        "  [API] API endpoints or integrations\n"
                        "  [DB] Database schema, migrations, queries\n"
                        "  [Infra] Infrastructure, deployment, configuration\n"
                        "  [Test] Testing, QA\n"
                        "  Choose the single most appropriate tag for each story.\n"
                        "- Title should be concise and action-oriented after the tag\n"
                        "- Description should explain what needs to be built and why\n"
                        "- Story points: assign 3 for most stories (standard scope); use 5 only if clearly larger; never exceed 5\n"
                        "- Order stories by logical implementation sequence (dependencies first)\n"
                        "- Generate as many stories as needed to fully cover the module"
                    ),
                },
            ],
        )

        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            raise ServiceUnavailableException("AI did not return a structured response. Please try again.")
        raw_stories: list[dict] = json.loads(tool_calls[0].function.arguments)["stories"]

        stories = await self.repository.bulk_create([
            Story(
                module_id=module_id,
                title=s["title"],
                description=s.get("description"),
                order=s.get("order", i),
                story_points=min(s.get("story_points", 3), 5),
                is_ai_generated=True,
            )
            for i, s in enumerate(raw_stories)
        ])
        return [StoryResponse.model_validate(s) for s in stories]
