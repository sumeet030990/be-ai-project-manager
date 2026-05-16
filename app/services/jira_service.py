import base64
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException


def _adf_paragraph(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


def _adf_heading(text: str, level: int = 3) -> dict[str, Any]:
    return {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": text}]}


def _build_description_adf(
    description: str | None,
    business_rules: str | None,
    acceptance_criteria: str | None,
) -> dict[str, Any] | None:
    content: list[dict[str, Any]] = []
    if description:
        content.append(_adf_paragraph(description))
    if business_rules:
        content.append(_adf_heading("Business Rules"))
        content.append(_adf_paragraph(business_rules))
    if acceptance_criteria:
        content.append(_adf_heading("Acceptance Criteria"))
        content.append(_adf_paragraph(acceptance_criteria))
    if not content:
        return None
    return {"type": "doc", "version": 1, "content": content}


@dataclass
class JiraIssue:
    key: str
    title: str
    description: str | None
    status: str
    story_points: int | None
    assignee_account_id: str | None = None
    assignee_display_name: str | None = None
    assignee_email: str | None = None


@dataclass
class JiraUser:
    account_id: str
    display_name: str
    email: str | None
    avatar_url: str | None
    active: bool


def _extract_adf_text(node: Any) -> str:
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        return "".join(_extract_adf_text(child) for child in node.get("content", []))
    if isinstance(node, list):
        return "".join(_extract_adf_text(child) for child in node)
    return ""


_JIRA_STATUS_MAP: dict[str, str] = {
    "to do": "draft",
    "open": "draft",
    "in progress": "in_progress",
    "in review": "review",
    "review": "review",
    "done": "done",
    "closed": "done",
    "resolved": "done",
}


def _map_jira_status(jira_status: str) -> str:
    return _JIRA_STATUS_MAP.get(jira_status.lower(), "draft")


def _extract_jira_error(response: httpx.Response) -> str:
    try:
        body = response.json()
        messages = body.get("errorMessages") or []
        errors = body.get("errors") or {}
        if messages:
            return messages[0]
        if errors:
            return "; ".join(f"{k}: {v}" for k, v in errors.items())
    except Exception:
        pass
    return response.text[:200]


class JiraService:
    def __init__(self) -> None:
        if not settings.JIRA_BASE_URL or not settings.JIRA_EMAIL or not settings.JIRA_API_KEY:
            raise ServiceUnavailableException(
                "JIRA integration is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_KEY."
            )
        credentials = base64.b64encode(f"{settings.JIRA_EMAIL}:{settings.JIRA_API_KEY}".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {credentials}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._base_url = settings.JIRA_BASE_URL.rstrip("/")

    def _build_fields(
        self,
        title: str,
        description: str | None,
        business_rules: str | None,
        acceptance_criteria: str | None,
        story_points: int | None,
    ) -> dict[str, Any]:
        fields: dict[str, Any] = {"summary": title}
        adf = _build_description_adf(description, business_rules, acceptance_criteria)
        if adf:
            fields["description"] = adf
        if story_points and settings.JIRA_STORY_POINTS_FIELD:
            fields[settings.JIRA_STORY_POINTS_FIELD] = story_points
        return fields

    async def fetch_all_issues(self, jira_project_key: str) -> list[JiraIssue]:
        if not jira_project_key:
            raise ServiceUnavailableException("JIRA project key is not configured for this project.")

        issues: list[JiraIssue] = []
        next_page_token: str | None = None
        fields = ["summary", "description", "status", settings.JIRA_STORY_POINTS_FIELD, "assignee"]

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                payload: dict[str, Any] = {
                    "jql": f"project = {jira_project_key} ORDER BY created DESC",
                    "fields": fields,
                    "maxResults": 100,
                }
                if next_page_token:
                    payload["nextPageToken"] = next_page_token

                response = await client.post(
                    f"{self._base_url}/rest/api/3/search/jql",
                    headers=self._headers,
                    json=payload,
                )
                if response.is_error:
                    raise ServiceUnavailableException(
                        f"JIRA fetch failed ({response.status_code}): {_extract_jira_error(response)}"
                    )

                body = response.json()
                batch = body.get("issues", [])
                for raw in batch:
                    f = raw.get("fields", {})
                    desc_node = f.get("description")
                    description = _extract_adf_text(desc_node).strip() or None
                    sp_raw = f.get(settings.JIRA_STORY_POINTS_FIELD)
                    story_points = int(sp_raw) if sp_raw is not None else None
                    assignee = f.get("assignee") or {}
                    issues.append(JiraIssue(
                        key=raw["key"],
                        title=f.get("summary", raw["key"]),
                        description=description,
                        status=_map_jira_status(f.get("status", {}).get("name", "")),
                        story_points=story_points,
                        assignee_account_id=assignee.get("accountId") or None,
                        assignee_display_name=assignee.get("displayName") or None,
                        assignee_email=assignee.get("emailAddress") or None,
                    ))

                next_page_token = body.get("nextPageToken")
                if not next_page_token or not batch:
                    break

        return issues

    async def fetch_issue_types(self, jira_project_key: str) -> list[dict[str, Any]]:
        if not jira_project_key:
            raise ServiceUnavailableException("JIRA project key is not configured for this project.")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._base_url}/rest/api/3/issue/createmeta/{jira_project_key}/issuetypes",
                headers=self._headers,
            )
            if response.is_error:
                raise ServiceUnavailableException(
                    f"JIRA issue types fetch failed ({response.status_code}): {_extract_jira_error(response)}"
                )
        return response.json().get("issueTypes", [])

    async def _resolve_issue_type(self, jira_project_key: str) -> str:
        try:
            types = await self.fetch_issue_types(jira_project_key)
            names = [t["name"] for t in types if not t.get("subtask", False)]
            if settings.JIRA_ISSUE_TYPE in names:
                return settings.JIRA_ISSUE_TYPE
            for preferred in ("Story", "Task", "Bug"):
                if preferred in names:
                    return preferred
            return names[0] if names else settings.JIRA_ISSUE_TYPE
        except Exception:
            return settings.JIRA_ISSUE_TYPE

    async def _resolve_epic_type(self, jira_project_key: str) -> str:
        try:
            types = await self.fetch_issue_types(jira_project_key)
            names = [t["name"] for t in types]
            if "Epic" in names:
                return "Epic"
        except Exception:
            pass
        return "Epic"

    async def create_issue(
        self,
        jira_project_key: str,
        title: str,
        description: str | None,
        business_rules: str | None,
        acceptance_criteria: str | None,
        story_points: int | None,
        parent_key: str | None = None,
        issue_type: str | None = None,
    ) -> str:
        if not jira_project_key:
            raise ServiceUnavailableException("JIRA project key is not configured for this project.")

        fields = self._build_fields(title, description, business_rules, acceptance_criteria, story_points)
        fields["project"] = {"key": jira_project_key}

        if issue_type:
            fields["issuetype"] = {"name": issue_type}
        elif parent_key:
            fields["issuetype"] = {"name": await self._resolve_issue_type(jira_project_key)}
        else:
            fields["issuetype"] = {"name": await self._resolve_issue_type(jira_project_key)}

        if parent_key:
            fields["parent"] = {"key": parent_key}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base_url}/rest/api/3/issue",
                headers=self._headers,
                json={"fields": fields},
            )
            if response.is_error:
                raise ServiceUnavailableException(f"JIRA create failed ({response.status_code}): {_extract_jira_error(response)}")
            return response.json()["key"]

    async def fetch_issue(self, issue_key: str) -> JiraIssue:
        fields = ["summary", "description", "status", settings.JIRA_STORY_POINTS_FIELD]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._base_url}/rest/api/3/issue/{issue_key}",
                headers=self._headers,
                params={"fields": ",".join(fields)},
            )
            if response.is_error:
                raise ServiceUnavailableException(
                    f"JIRA fetch issue failed ({response.status_code}): {_extract_jira_error(response)}"
                )
        raw = response.json()
        f = raw.get("fields", {})
        desc_node = f.get("description")
        description = _extract_adf_text(desc_node).strip() or None
        sp_raw = f.get(settings.JIRA_STORY_POINTS_FIELD)
        story_points = int(sp_raw) if sp_raw is not None else None
        return JiraIssue(
            key=raw["key"],
            title=f.get("summary", raw["key"]),
            description=description,
            status=_map_jira_status(f.get("status", {}).get("name", "")),
            story_points=story_points,
        )

    async def delete_issue(self, issue_key: str) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self._base_url}/rest/api/3/issue/{issue_key}",
                headers=self._headers,
            )
            if response.is_error:
                raise ServiceUnavailableException(f"JIRA delete failed ({response.status_code}): {_extract_jira_error(response)}")

    async def update_issue(
        self,
        issue_key: str,
        title: str,
        description: str | None,
        business_rules: str | None,
        acceptance_criteria: str | None,
        story_points: int | None,
    ) -> None:
        fields = self._build_fields(title, description, business_rules, acceptance_criteria, story_points)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self._base_url}/rest/api/3/issue/{issue_key}",
                headers=self._headers,
                json={"fields": fields},
            )
            if response.is_error:
                raise ServiceUnavailableException(f"JIRA update failed ({response.status_code}): {_extract_jira_error(response)}")

    async def fetch_project_members(self, jira_project_key: str) -> list[JiraUser]:
        if not jira_project_key:
            raise ServiceUnavailableException("JIRA project key is not configured for this project.")

        users: list[JiraUser] = []
        seen: set[str] = set()
        start_at = 0
        max_results = 100

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                response = await client.get(
                    f"{self._base_url}/rest/api/3/user/assignable/search",
                    headers=self._headers,
                    params={"project": jira_project_key, "startAt": start_at, "maxResults": max_results},
                )
                if response.is_error:
                    raise ServiceUnavailableException(
                        f"JIRA members fetch failed ({response.status_code}): {_extract_jira_error(response)}"
                    )
                batch = response.json()
                if not batch:
                    break
                for raw in batch:
                    account_id = raw.get("accountId", "")
                    if not account_id or account_id in seen:
                        continue
                    seen.add(account_id)
                    avatar_urls = raw.get("avatarUrls", {})
                    users.append(JiraUser(
                        account_id=account_id,
                        display_name=raw.get("displayName", ""),
                        email=raw.get("emailAddress") or None,
                        avatar_url=avatar_urls.get("48x48") or None,
                        active=raw.get("active", True),
                    ))
                if len(batch) < max_results:
                    break
                start_at += max_results

        return users
