import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_client import get_project_ai_client
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException, ServiceUnavailableException
from app.repositories.project_repository import ProjectRepository
from app.repositories.sprint_repository import SprintRepository
from app.repositories.story_repository import StoryRepository
from app.schemas.sprint import (
    ActiveSprintResponse,
    BacklogFeatureGroup,
    BacklogResponse,
    SprintAIPlanRequest,
    SprintAIPlanResult,
    SprintBoardColumns,
    SprintCreate,
    SprintResponse,
    SprintStoriesRequest,
    SprintSyncFailure,
    SprintSyncResult,
    SprintUpdate,
)
from app.schemas.story import StoryResponse
from database.models.sprint import Sprint


_STATUS_TO_COLUMN = {
    "draft": "todo",
    "approved": "todo",
    "rejected": "todo",
    "in_progress": "in_progress",
    "review": "in_review",
    "done": "done",
}

_AI_PLAN_SPRINT_TOOL: Any = {
    "type": "function",
    "function": {
        "name": "plan_sprint",
        "description": "Select stories from the backlog to fill the sprint based on capacity and goal.",
        "parameters": {
            "type": "object",
            "properties": {
                "selected_story_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs of stories selected for the sprint, in priority order.",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of why these stories were selected.",
                },
            },
            "required": ["selected_story_ids", "reasoning"],
        },
    },
}


class SprintService:
    def __init__(self, session: AsyncSession):
        self.repository = SprintRepository(session)
        self.story_repository = StoryRepository(session)
        self.project_repository = ProjectRepository(session)

    async def _get_project_or_404(self, project_id: uuid.UUID):
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        return project

    async def _get_sprint_or_404(self, project_id: uuid.UUID, sprint_id: uuid.UUID) -> Sprint:
        sprint = await self.repository.get_by_project_and_id(project_id, sprint_id)
        if not sprint:
            raise NotFoundException("Sprint", str(sprint_id))
        return sprint

    async def _require_jira_board_id(self, project_id: uuid.UUID) -> int:
        project = await self._get_project_or_404(project_id)
        if not project.jira_board_id:
            raise ServiceUnavailableException(
                "JIRA board ID is not configured for this project. Set jira_board_id on the project."
            )
        return project.jira_board_id

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def list_sprints(self, project_id: uuid.UUID) -> list[SprintResponse]:
        await self._get_project_or_404(project_id)
        sprints = await self.repository.get_all_by_project(project_id)
        return [SprintResponse.model_validate(s) for s in sprints]

    async def get_sprint(self, project_id: uuid.UUID, sprint_id: uuid.UUID) -> SprintResponse:
        sprint = await self._get_sprint_or_404(project_id, sprint_id)
        return SprintResponse.model_validate(sprint)

    async def create_sprint(self, project_id: uuid.UUID, payload: SprintCreate) -> SprintResponse:
        await self._get_project_or_404(project_id)
        sprint = Sprint(project_id=project_id, **payload.model_dump())
        sprint = await self.repository.create(sprint)
        return SprintResponse.model_validate(sprint)

    async def update_sprint(self, project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintUpdate) -> SprintResponse:
        sprint = await self._get_sprint_or_404(project_id, sprint_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(sprint, field, value)
        sprint = await self.repository.update(sprint)
        return SprintResponse.model_validate(sprint)

    async def delete_sprint(self, project_id: uuid.UUID, sprint_id: uuid.UUID) -> None:
        sprint = await self._get_sprint_or_404(project_id, sprint_id)
        if sprint.status == "active":
            raise BadRequestException("Cannot delete an active sprint. Complete it first.")
        await self.repository.delete(sprint)

    # ── Sprint lifecycle ──────────────────────────────────────────────────────

    async def start_sprint(self, project_id: uuid.UUID, sprint_id: uuid.UUID) -> SprintResponse:
        sprint = await self._get_sprint_or_404(project_id, sprint_id)
        if sprint.status != "planning":
            raise BadRequestException(f"Sprint is already '{sprint.status}'. Only planning sprints can be started.")

        existing_active = await self.repository.get_active_sprint(project_id)
        if existing_active and existing_active.id != sprint_id:
            raise ConflictException(
                f"Sprint '{existing_active.name}' is already active. Complete it before starting a new one."
            )

        sprint.status = "active"
        sprint = await self.repository.update(sprint)
        return SprintResponse.model_validate(sprint)

    async def complete_sprint(self, project_id: uuid.UUID, sprint_id: uuid.UUID) -> SprintResponse:
        """Complete the sprint. Incomplete stories are moved back to the backlog (removed from sprint)."""
        sprint = await self._get_sprint_or_404(project_id, sprint_id)
        if sprint.status != "active":
            raise BadRequestException("Only an active sprint can be completed.")

        stories = await self.repository.get_stories_in_sprint(sprint_id)
        incomplete_ids = [s.id for s in stories if s.status != "done"]
        if incomplete_ids:
            await self.repository.remove_stories(sprint_id, incomplete_ids)

        sprint.status = "completed"
        sprint = await self.repository.update(sprint)
        return SprintResponse.model_validate(sprint)

    # ── Backlog view ──────────────────────────────────────────────────────────

    async def get_backlog(self, project_id: uuid.UUID) -> BacklogResponse:
        await self._get_project_or_404(project_id)
        stories = await self.repository.get_backlog_stories(project_id)

        groups: dict[uuid.UUID, BacklogFeatureGroup] = {}
        total_points = 0

        for story in stories:
            fid = story.feature_id
            if fid not in groups:
                epic = story.feature.epic if story.feature else None
                groups[fid] = BacklogFeatureGroup(
                    feature_id=fid,
                    feature_name=story.feature.name if story.feature else "",
                    jira_epic_key=epic.jira_epic_key if epic else None,
                    stories=[],
                )
            groups[fid].stories.append(StoryResponse.model_validate(story))
            total_points += story.story_points or 0

        return BacklogResponse(
            features=list(groups.values()),
            total_stories=len(stories),
            total_points=total_points,
        )

    # ── Active Sprint board ───────────────────────────────────────────────────

    async def get_active_sprint_board(self, project_id: uuid.UUID) -> ActiveSprintResponse:
        sprint = await self.repository.get_active_sprint(project_id)
        if not sprint:
            raise NotFoundException("Active sprint", f"project {project_id}")

        stories = await self.repository.get_stories_in_sprint(sprint.id)

        columns: dict[str, list[StoryResponse]] = defaultdict(list)
        total_points = 0
        completed_points = 0

        for story in stories:
            col = _STATUS_TO_COLUMN.get(story.status, "todo")
            columns[col].append(StoryResponse.model_validate(story))
            pts = story.story_points or 0
            total_points += pts
            if story.status == "done":
                completed_points += pts

        return ActiveSprintResponse(
            sprint=SprintResponse.model_validate(sprint),
            columns=SprintBoardColumns(
                todo=columns.get("todo", []),
                in_progress=columns.get("in_progress", []),
                in_review=columns.get("in_review", []),
                done=columns.get("done", []),
            ),
            total_points=total_points,
            completed_points=completed_points,
        )

    # ── Story assignment ──────────────────────────────────────────────────────

    async def add_stories(self, project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintStoriesRequest) -> SprintResponse:
        sprint = await self._get_sprint_or_404(project_id, sprint_id)
        if sprint.status == "completed":
            raise BadRequestException("Cannot add stories to a completed sprint.")
        await self.repository.add_stories(sprint_id, payload.story_ids)
        return SprintResponse.model_validate(sprint)

    async def remove_stories(self, project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintStoriesRequest) -> SprintResponse:
        sprint = await self._get_sprint_or_404(project_id, sprint_id)
        await self.repository.remove_stories(sprint_id, payload.story_ids)
        return SprintResponse.model_validate(sprint)

    async def get_sprint_stories(self, project_id: uuid.UUID, sprint_id: uuid.UUID) -> list[StoryResponse]:
        await self._get_sprint_or_404(project_id, sprint_id)
        stories = await self.repository.get_stories_in_sprint(sprint_id)
        return [StoryResponse.model_validate(s) for s in stories]

    # ── JIRA Sprint Sync ──────────────────────────────────────────────────────

    async def sync_from_jira(self, project_id: uuid.UUID) -> SprintSyncResult:
        from app.services.jira_service import JiraService

        board_id = await self._require_jira_board_id(project_id)
        jira = JiraService()
        raw_sprints = await jira.fetch_sprints(board_id)

        created: list[SprintResponse] = []
        updated: list[SprintResponse] = []
        failed: list[SprintSyncFailure] = []

        _jira_to_local_status = {
            "future": "planning",
            "active": "active",
            "closed": "completed",
        }

        for raw in raw_sprints:
            jira_sprint_id: int = raw["id"]
            try:
                local_status = _jira_to_local_status.get(raw.get("state", "future"), "planning")
                existing = await self.repository.get_by_jira_sprint_id(jira_sprint_id)

                if existing:
                    existing.name = raw.get("name", existing.name)
                    existing.goal = raw.get("goal") or existing.goal
                    existing.status = local_status
                    existing = await self.repository.update(existing)
                    sprint_response = SprintResponse.model_validate(existing)
                    updated.append(sprint_response)
                    sprint_local_id = existing.id
                else:
                    sprint = Sprint(
                        project_id=project_id,
                        name=raw.get("name", f"Sprint {jira_sprint_id}"),
                        goal=raw.get("goal") or None,
                        status=local_status,
                        jira_sprint_id=jira_sprint_id,
                    )
                    sprint = await self.repository.create(sprint)
                    sprint_response = SprintResponse.model_validate(sprint)
                    created.append(sprint_response)
                    sprint_local_id = sprint.id

                # Sync issues for this sprint into sprint_stories
                issues = await jira.fetch_sprint_issues(jira_sprint_id)
                jira_keys = [i.key for i in issues]
                if jira_keys:
                    stories = await self.story_repository.get_by_jira_keys(jira_keys)
                    story_ids = [s.id for s in stories]
                    if story_ids:
                        await self.repository.add_stories(sprint_local_id, story_ids)

            except Exception as exc:
                failed.append(SprintSyncFailure(
                    jira_sprint_id=jira_sprint_id,
                    name=raw.get("name", str(jira_sprint_id)),
                    error=str(exc),
                ))

        return SprintSyncResult(
            fetched=len(raw_sprints),
            created=created,
            updated=updated,
            failed=failed,
        )

    async def push_sprint_to_jira(self, project_id: uuid.UUID, sprint_id: uuid.UUID) -> SprintResponse:
        from app.services.jira_service import JiraService

        sprint = await self._get_sprint_or_404(project_id, sprint_id)
        board_id = await self._require_jira_board_id(project_id)
        jira = JiraService()

        start_str = sprint.start_date.isoformat() if sprint.start_date else None
        end_str = sprint.end_date.isoformat() if sprint.end_date else None

        if sprint.jira_sprint_id:
            await jira.update_sprint_status(
                sprint.jira_sprint_id,
                "active" if sprint.status == "active" else "closed" if sprint.status == "completed" else "future",
            )
        else:
            jira_sprint_id = await jira.create_sprint(
                board_id=board_id,
                name=sprint.name,
                goal=sprint.goal,
                start_date=start_str,
                end_date=end_str,
            )
            sprint.jira_sprint_id = jira_sprint_id
            sprint = await self.repository.update(sprint)

        stories = await self.repository.get_stories_in_sprint(sprint_id)
        jira_keys = [s.jira_issue_key for s in stories if s.jira_issue_key]
        if jira_keys and sprint.jira_sprint_id:
            await jira.add_issues_to_sprint(sprint.jira_sprint_id, jira_keys)

        return SprintResponse.model_validate(sprint)

    # ── AI Sprint Planning ────────────────────────────────────────────────────

    async def ai_plan_sprint(self, project_id: uuid.UUID, sprint_id: uuid.UUID, payload: SprintAIPlanRequest) -> SprintAIPlanResult:
        sprint = await self._get_sprint_or_404(project_id, sprint_id)
        all_backlog_stories = await self.repository.get_backlog_stories(project_id)

        if not all_backlog_stories:
            raise BadRequestException("No backlog stories available for AI planning.")

        # Filter to selected features when specified; keep all stories as context
        if payload.feature_ids:
            feature_id_set = set(payload.feature_ids)
            focused_stories = [s for s in all_backlog_stories if s.feature_id in feature_id_set]
            other_stories = [s for s in all_backlog_stories if s.feature_id not in feature_id_set]
        else:
            focused_stories = all_backlog_stories
            other_stories = []

        if not focused_stories:
            raise BadRequestException("No backlog stories found in the selected features.")

        def _story_line(s) -> str:
            desc = s.description or "N/A"
            if len(desc) > 120:
                desc = desc[:120] + "..."
            feature_name = s.feature.name if s.feature else "Unknown"
            return f"- ID: {s.id} | [{s.story_points or '?'} pts] [{feature_name}] {s.title}\n  Description: {desc}"

        focused_text = "\n".join(_story_line(s) for s in focused_stories)

        feature_focus_note = ""
        if payload.feature_ids:
            focused_feature_names = list({s.feature.name for s in focused_stories if s.feature})
            feature_focus_note = (
                f"IMPORTANT: The user wants to focus this sprint on the following feature(s): "
                f"{', '.join(focused_feature_names)}. "
                "Prioritize stories from these features. "
            )
            if other_stories:
                other_text = "\n".join(_story_line(s) for s in other_stories)
                story_list_section = (
                    f"Focused feature stories (prioritize these):\n{focused_text}\n\n"
                    f"Other backlog stories (include only if capacity allows and they complement the focus):\n{other_text}"
                )
            else:
                story_list_section = f"Available backlog stories:\n{focused_text}"
        else:
            story_list_section = f"Available backlog stories:\n{focused_text}"

        config_id = uuid.UUID(payload.config_id) if payload.config_id else None
        ai_client = await get_project_ai_client(project_id, self.repository.session, config_id=config_id)

        result = await ai_client.chat_with_tools(
            tools=[_AI_PLAN_SPRINT_TOOL],
            tool_choice={"type": "function", "function": {"name": "plan_sprint"}},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert agile project manager helping plan a sprint. "
                        "Your job is to select the most valuable and coherent set of stories from the backlog "
                        "that fits within the sprint capacity without exceeding it. "
                        + feature_focus_note
                        + "Prioritize stories with higher story point values that form a complete feature, "
                        "and prefer lower-numbered IDs when story priority is equal."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Sprint: {sprint.name}\n"
                        f"Sprint goal: {sprint.goal or 'No specific goal set.'}\n"
                        f"Sprint capacity: {payload.capacity} story points\n\n"
                        + (f"Additional context: {payload.context}\n\n" if payload.context else "")
                        + f"{story_list_section}\n\n"
                        "Select stories that:\n"
                        "1. Together do NOT exceed the capacity\n"
                        "2. Are aligned with the sprint goal\n"
                        "3. Form a coherent set of work (prefer complete features over partial ones)\n"
                        "4. Are ordered by implementation priority (dependencies first)\n"
                        "Return only the story IDs in order."
                    ),
                },
            ],
        )

        selected_ids_raw: list[str] = result.arguments.get("selected_story_ids", [])
        reasoning: str = result.arguments.get("reasoning", "")

        id_to_story = {str(s.id): s for s in all_backlog_stories}
        selected_stories = [
            id_to_story[sid] for sid in selected_ids_raw if sid in id_to_story
        ]

        total_points = sum(s.story_points or 0 for s in selected_stories)

        return SprintAIPlanResult(
            selected_stories=[StoryResponse.model_validate(s) for s in selected_stories],
            total_points=total_points,
            reasoning=reasoning,
        )
