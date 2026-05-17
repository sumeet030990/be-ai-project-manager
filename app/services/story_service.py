import json
import math
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_client import get_project_ai_client
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException, ServiceUnavailableException
from app.repositories.module_repository import ModuleRepository
from app.repositories.project_plugin_repository import ProjectPluginRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.project_tech_stack_repository import ProjectTechStackRepository
from app.repositories.story_repository import StoryRepository
from app.schemas.common import PaginatedResponse
from app.schemas.story import JiraSyncFailure, JiraSyncResult, StoryCreate, StoryRefineRequest, StoryRefineResponse, StoryResponse, StoryUpdate
from database.models.story import Story

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
        self.project_repository = ProjectRepository(session)
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

    async def _get_jira_project_key(self, project_id: uuid.UUID) -> str:
        project = await self.project_repository.get_by_id(project_id)
        if not project or not project.jira_project_key:
            raise ServiceUnavailableException("JIRA project key is not configured for this project.")
        return project.jira_project_key

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

    async def delete_story(self, module_id: uuid.UUID, story_id: uuid.UUID, delete_remote: bool = False) -> None:
        from app.services.jira_service import JiraService

        story = await self._get_story_or_404(module_id, story_id)
        if delete_remote and story.jira_issue_key:
            jira = JiraService()
            await jira.delete_issue(story.jira_issue_key)
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

        config_id = uuid.UUID(payload.config_id) if payload.config_id else None
        ai_client = await get_project_ai_client(module.project_id, self.repository.session, config_id=config_id)
        result = await ai_client.chat_with_tools(
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

        refined = StoryRefineResponse(**result.arguments)
        for field, value in refined.model_dump().items():
            setattr(story, field, value)
        story = await self.repository.update(story)
        return StoryResponse.model_validate(story)

    # ── JIRA Sync ────────────────────────────────────────────────────────────

    async def sync_stories_to_jira(self, module_id: uuid.UUID) -> JiraSyncResult:
        from app.services.jira_service import JiraService

        module = await self._get_module_or_404(module_id)
        jira_project_key = await self._get_jira_project_key(module.project_id)

        jira = JiraService()
        jira_issues = await jira.fetch_all_issues(jira_project_key)
        existing_keys = await self.repository.get_existing_jira_keys()

        new_issues = [issue for issue in jira_issues if issue.key not in existing_keys]
        existing_issues = [issue for issue in jira_issues if issue.key in existing_keys]

        # Build assignee map: link local users to their JIRA accounts for all issues
        assignee_map, users_linked = await self._build_assignee_map(jira_issues)

        imported: list[StoryResponse] = []
        updated: list[StoryResponse] = []
        failed: list[JiraSyncFailure] = []

        for order, issue in enumerate(new_issues):
            try:
                user = assignee_map.get(issue.assignee_account_id) if issue.assignee_account_id else None
                story = Story(
                    module_id=module_id,
                    title=issue.title,
                    description=issue.description,
                    status=issue.status,
                    story_points=issue.story_points,
                    order=order,
                    jira_issue_key=issue.key,
                    assignee_id=user.id if user else None,
                )
                story = await self.repository.create(story)
                imported.append(StoryResponse.model_validate(story))
            except Exception as exc:
                failed.append(JiraSyncFailure(jira_key=issue.key, title=issue.title, error=str(exc)))

        if existing_issues:
            existing_issue_map = {issue.key: issue for issue in existing_issues}
            stories_to_update = await self.repository.get_by_jira_keys(list(existing_issue_map.keys()))
            for story in stories_to_update:
                jira_issue = existing_issue_map[story.jira_issue_key]
                story.status = jira_issue.status
                story.story_points = jira_issue.story_points
                user = assignee_map.get(jira_issue.assignee_account_id) if jira_issue.assignee_account_id else None
                if user:
                    story.assignee_id = user.id
                try:
                    story = await self.repository.update(story)
                    updated.append(StoryResponse.model_validate(story))
                except Exception as exc:
                    failed.append(JiraSyncFailure(jira_key=story.jira_issue_key, title=story.title, error=str(exc)))

        return JiraSyncResult(fetched=len(jira_issues), imported=imported, updated=updated, skipped=0, failed=failed, users_linked=users_linked)

    async def _build_assignee_map(self, issues: list) -> tuple[dict, list]:
        from app.schemas.user import UserResponse as UserResponseSchema
        from app.repositories.user_repository import UserRepository
        from database.models.user import User as UserModel

        user_repo = UserRepository(self.repository.session)

        # Collect unique assignees with both email and account_id
        seen: set[str] = set()
        assignees: list[tuple[str, str]] = []  # (email, account_id)
        for issue in issues:
            if issue.assignee_email and issue.assignee_account_id and issue.assignee_email not in seen:
                seen.add(issue.assignee_email)
                assignees.append((issue.assignee_email, issue.assignee_account_id))

        if not assignees:
            return {}, []

        emails = [a[0] for a in assignees]
        local_users = await user_repo.get_by_emails(emails)
        email_to_user: dict[str, UserModel] = {u.email: u for u in local_users}

        # Link jira_account_id where missing, build account_id → user map
        account_id_to_user: dict[str, UserModel] = {}
        users_linked: list = []

        for email, account_id in assignees:
            user = email_to_user.get(email)
            if not user:
                continue
            if not user.jira_account_id:
                user.jira_account_id = account_id
                user = await user_repo.update(user)
                users_linked.append(UserResponseSchema.model_validate(user))
            account_id_to_user[account_id] = user

        return account_id_to_user, users_linked

    async def pull_story_from_jira(self, module_id: uuid.UUID, story_id: uuid.UUID) -> StoryResponse:
        from app.services.jira_service import JiraService

        story = await self._get_story_or_404(module_id, story_id)
        if not story.jira_issue_key:
            raise BadRequestException("Story is not linked to a JIRA issue.")

        jira = JiraService()
        issue = await jira.fetch_issue(story.jira_issue_key)
        story.title = issue.title
        story.description = issue.description
        story.status = issue.status
        story.story_points = issue.story_points
        story = await self.repository.update(story)
        return StoryResponse.model_validate(story)

    async def create_story_in_jira(self, module_id: uuid.UUID, story_id: uuid.UUID) -> StoryResponse:
        from app.services.jira_service import JiraService

        story = await self._get_story_or_404(module_id, story_id)
        if story.jira_issue_key:
            raise ConflictException(f"Story is already linked to JIRA issue {story.jira_issue_key}.")

        module = await self._get_module_or_404(module_id)
        jira_project_key = await self._get_jira_project_key(module.project_id)

        jira = JiraService()

        if not module.jira_epic_key:
            epic_key = await jira.create_issue(
                jira_project_key=jira_project_key,
                title=module.name,
                description=module.description,
                business_rules=None,
                acceptance_criteria=None,
                story_points=None,
                issue_type=await jira._resolve_epic_type(jira_project_key),
            )
            module.jira_epic_key = epic_key
            await self.module_repository.update(module)

        key = await jira.create_issue(
            jira_project_key=jira_project_key,
            title=story.title,
            description=story.description,
            business_rules=story.business_rules,
            acceptance_criteria=story.acceptance_criteria,
            story_points=story.story_points,
            parent_key=module.jira_epic_key,
        )
        story.jira_issue_key = key
        story = await self.repository.update(story)
        return StoryResponse.model_validate(story)

    async def update_story_in_jira(self, module_id: uuid.UUID, story_id: uuid.UUID) -> StoryResponse:
        from app.services.jira_service import JiraService

        story = await self._get_story_or_404(module_id, story_id)
        if not story.jira_issue_key:
            raise BadRequestException("Story is not linked to a JIRA issue. Create it in JIRA first.")

        jira = JiraService()
        await jira.update_issue(
            issue_key=story.jira_issue_key,
            title=story.title,
            description=story.description,
            business_rules=story.business_rules,
            acceptance_criteria=story.acceptance_criteria,
            story_points=story.story_points,
        )
        return StoryResponse.model_validate(story)

    async def delete_story_from_jira(self, module_id: uuid.UUID, story_id: uuid.UUID) -> StoryResponse:
        from app.services.jira_service import JiraService

        story = await self._get_story_or_404(module_id, story_id)
        if not story.jira_issue_key:
            raise BadRequestException("Story is not linked to a JIRA issue.")

        jira = JiraService()
        await jira.delete_issue(story.jira_issue_key)
        story.jira_issue_key = None
        story = await self.repository.update(story)
        return StoryResponse.model_validate(story)

    # ── AI Generation ─────────────────────────────────────────────────────────

    async def generate_stories(self, project_id: uuid.UUID, module_id: uuid.UUID, context: str | None = None, config_id: uuid.UUID | None = None) -> list[StoryResponse]:
        module = await self.module_repository.get_by_project_and_id(project_id, module_id)
        if not module:
            raise NotFoundException("Module", str(module_id))

        tech_stacks, _ = await self.tech_stack_repository.get_all_by_project(project_id, skip=0, limit=500)
        plugins, _ = await self.plugin_repository.get_all_by_project(project_id, skip=0, limit=500)
        tech_context = _build_tech_context(tech_stacks, plugins)

        ai_client = await get_project_ai_client(project_id, self.repository.session, config_id=config_id)
        result = await ai_client.chat_with_tools(
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

        raw_stories: list[dict] = result.arguments["stories"]

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
