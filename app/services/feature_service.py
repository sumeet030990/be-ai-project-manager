import math
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_client import get_project_ai_client
from app.core.exceptions import NotFoundException
from app.repositories.epic_repository import EpicRepository
from app.repositories.feature_repository import FeatureRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.project_plugin_repository import ProjectPluginRepository
from app.repositories.project_tech_stack_repository import ProjectTechStackRepository
from app.repositories.story_repository import StoryRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.feature import FeatureCreate, FeatureGenerateRequest, FeatureRefineRequest, FeatureRefineResponse, FeatureResponse, FeatureUpdate
from database.models.feature import Feature


_GENERATE_FEATURES_TOOL: Any = {
    "type": "function",
    "function": {
        "name": "save_features",
        "description": "Save the generated features for the epic.",
        "parameters": {
            "type": "object",
            "properties": {
                "features": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Short, action-oriented feature name (e.g. 'User Authentication', 'Payment Processing')."},
                            "description": {"type": "string", "description": "Clear explanation of what this feature encompasses and the value it delivers."},
                            "order": {"type": "integer"},
                        },
                        "required": ["name", "description", "order"],
                    },
                }
            },
            "required": ["features"],
        },
    },
}

_REFINE_FEATURE_TOOL: Any = {
    "type": "function",
    "function": {
        "name": "refine_feature",
        "description": "Save the refined feature details.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Detailed description of the feature — what it covers, its purpose, and its scope within the product.",
                },
                "business_rules": {
                    "type": "string",
                    "description": "Business logic, constraints, and rules this feature must satisfy.",
                },
                "acceptance_criteria": {
                    "type": "string",
                    "description": "Clear, testable conditions that must be met for this feature to be considered complete.",
                },
            },
            "required": ["description", "business_rules", "acceptance_criteria"],
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


class FeatureService:
    def __init__(self, session: AsyncSession):
        self.repository = FeatureRepository(session)
        self.epic_repository = EpicRepository(session)
        self.story_repository = StoryRepository(session)
        self.user_repository = UserRepository(session)
        self.project_repository = ProjectRepository(session)
        self.tech_stack_repository = ProjectTechStackRepository(session)
        self.plugin_repository = ProjectPluginRepository(session)

    async def list_features(self, epic_id: uuid.UUID, page: int, size: int) -> PaginatedResponse[FeatureResponse]:
        if not await self.epic_repository.get_by_id(epic_id):
            raise NotFoundException("Epic", str(epic_id))
        skip = (page - 1) * size
        items, total = await self.repository.get_all_by_epic(epic_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[FeatureResponse.model_validate(f) for f in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_feature(self, epic_id: uuid.UUID, feature_id: uuid.UUID) -> FeatureResponse:
        feature = await self.repository.get_by_epic_and_id(epic_id, feature_id)
        if not feature:
            raise NotFoundException("Feature", str(feature_id))
        return FeatureResponse.model_validate(feature)

    async def create_feature(self, epic_id: uuid.UUID, payload: FeatureCreate) -> FeatureResponse:
        if not await self.epic_repository.get_by_id(epic_id):
            raise NotFoundException("Epic", str(epic_id))
        if not await self.user_repository.get_by_id(payload.created_by):
            raise NotFoundException("User", str(payload.created_by))
        feature = Feature(epic_id=epic_id, **payload.model_dump())
        feature = await self.repository.create(feature)
        return FeatureResponse.model_validate(feature)

    async def update_feature(self, epic_id: uuid.UUID, feature_id: uuid.UUID, payload: FeatureUpdate) -> FeatureResponse:
        feature = await self.repository.get_by_epic_and_id(epic_id, feature_id)
        if not feature:
            raise NotFoundException("Feature", str(feature_id))
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(feature, field, value)
        feature = await self.repository.update(feature)
        return FeatureResponse.model_validate(feature)

    async def delete_feature(self, epic_id: uuid.UUID, feature_id: uuid.UUID, delete_remote: bool = False) -> None:
        from app.services.jira_service import JiraService

        feature = await self.repository.get_by_epic_and_id(epic_id, feature_id)
        if not feature:
            raise NotFoundException("Feature", str(feature_id))
        if delete_remote:
            linked_stories = await self.story_repository.get_jira_linked_stories_by_feature(feature_id)
            if linked_stories:
                jira = JiraService()
                for story in linked_stories:
                    await jira.delete_issue(story.jira_issue_key)
        await self.repository.delete(feature)

    # ── AI Generation ─────────────────────────────────────────────────────────

    async def generate_features(self, epic_id: uuid.UUID, payload: FeatureGenerateRequest) -> list[FeatureResponse]:
        epic = await self.epic_repository.get_by_id(epic_id)
        if not epic:
            raise NotFoundException("Epic", str(epic_id))

        project = await self.project_repository.get_by_id(epic.project_id)
        tech_stacks, _ = await self.tech_stack_repository.get_all_by_project(epic.project_id, skip=0, limit=500)
        plugins, _ = await self.plugin_repository.get_all_by_project(epic.project_id, skip=0, limit=500)
        tech_context = _build_tech_context(tech_stacks, plugins)

        config_id = uuid.UUID(payload.config_id) if payload.config_id else None
        ai_client = await get_project_ai_client(epic.project_id, self.repository.session, config_id=config_id)

        result = await ai_client.chat_with_tools(
            tools=[_GENERATE_FEATURES_TOOL],
            tool_choice={"type": "function", "function": {"name": "save_features"}},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software product manager who breaks epics into well-scoped features "
                        "for development teams.\n\n"
                        + (f"Project context:\n{project.project_info}\n\n" if project and project.project_info else "")
                        + f"Project tech stack:\n{tech_context}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Break down the following epic into features.\n\n"
                        f"Epic: {epic.name}\n"
                        f"Epic description: {epic.description or 'No description provided.'}\n\n"
                        + (f"Additional context:\n{payload.context}\n\n" if payload.context else "")
                        + "Rules:\n"
                        "- Each feature should be a coherent, deliverable chunk of functionality\n"
                        "- Features must align with the project description and tech stack\n"
                        "- Name should be concise and descriptive (e.g. 'User Authentication', 'Payment Processing')\n"
                        "- Description should explain what the feature covers and the value it delivers\n"
                        "- Order features by logical implementation sequence (dependencies first)\n"
                        "- Generate as many features as needed to fully cover the epic"
                    ),
                },
            ],
        )

        raw_features: list[dict] = result.arguments["features"]
        created_by = epic.created_by

        features = []
        for i, f in enumerate(raw_features):
            feature = Feature(
                epic_id=epic_id,
                created_by=created_by,
                name=f["name"],
                description=f.get("description"),
                order=f.get("order", i),
                is_ai_generated=True,
            )
            feature = await self.repository.create(feature)
            features.append(feature)

        return [FeatureResponse.model_validate(f) for f in features]

    async def refine_feature(self, epic_id: uuid.UUID, feature_id: uuid.UUID, payload: FeatureRefineRequest) -> FeatureResponse:
        feature = await self.repository.get_by_epic_and_id(epic_id, feature_id)
        if not feature:
            raise NotFoundException("Feature", str(feature_id))

        epic = await self.epic_repository.get_by_id(epic_id)
        if not epic:
            raise NotFoundException("Epic", str(epic_id))

        tech_stacks, _ = await self.tech_stack_repository.get_all_by_project(epic.project_id, skip=0, limit=500)
        plugins, _ = await self.plugin_repository.get_all_by_project(epic.project_id, skip=0, limit=500)
        tech_context = _build_tech_context(tech_stacks, plugins)

        is_refinement = any([feature.description, feature.business_rules, feature.acceptance_criteria])

        if is_refinement:
            current_state = (
                f"Current feature details (already refined — update based on the manager's instructions):\n"
                f"Description: {feature.description or '-'}\n"
                f"Business rules: {feature.business_rules or '-'}\n"
                f"Acceptance criteria: {feature.acceptance_criteria or '-'}\n\n"
            )
        else:
            current_state = ""

        manager_note = (
            f"Manager's instructions: {payload.context}\n\n"
            if payload.context else
            "No additional instructions — generate full details from scratch.\n\n"
        )

        config_id = uuid.UUID(payload.config_id) if payload.config_id else None
        ai_client = await get_project_ai_client(epic.project_id, self.repository.session, config_id=config_id)

        result = await ai_client.chat_with_tools(
            tools=[_REFINE_FEATURE_TOOL],
            tool_choice={"type": "function", "function": {"name": "refine_feature"}},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software product manager and business analyst. "
                        "You enrich features with detailed requirements to help development teams plan and implement them precisely.\n\n"
                        f"Project tech stack:\n{tech_context}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Epic: {epic.name}\n"
                        f"Epic description: {epic.description or 'No description provided.'}\n\n"
                        f"Feature: {feature.name}\n"
                        f"Feature description: {feature.description or 'No description provided.'}\n\n"
                        f"{current_state}"
                        f"{manager_note}"
                        "Provide:\n"
                        "- A detailed description of what this feature encompasses and its scope\n"
                        "- Business rules and constraints the implementation must satisfy\n"
                        "- Clear, testable acceptance criteria for the feature"
                    ),
                },
            ],
        )

        refined = FeatureRefineResponse(**result.arguments)
        feature.description = refined.description
        feature.business_rules = refined.business_rules
        feature.acceptance_criteria = refined.acceptance_criteria
        feature = await self.repository.update(feature)
        return FeatureResponse.model_validate(feature)
