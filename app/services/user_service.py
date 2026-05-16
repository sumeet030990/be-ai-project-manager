import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.core.security import hash_password
from database.models.user import User
from app.repositories.company_repository import CompanyRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectResponse
from app.schemas.user import (
    JiraUserPreview,
    JiraUserSyncFailure,
    JiraUserSyncRequest,
    JiraUserSyncResult,
    UserCreate,
    UserResponse,
    UserUpdate,
)


class UserService:
    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)
        self.role_repository = RoleRepository(session)
        self.company_repository = CompanyRepository(session)
        self.project_repository = ProjectRepository(session)

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundException("User", str(user_id))
        return UserResponse.model_validate(user)

    async def list_users(self, page: int, size: int) -> PaginatedResponse[UserResponse]:
        skip = (page - 1) * size
        items, total = await self.repository.get_all(skip=skip, limit=size)
        return PaginatedResponse(
            items=[UserResponse.model_validate(u) for u in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def create_user(self, payload: UserCreate) -> UserResponse:
        if await self.repository.get_by_email(payload.email):
            raise ConflictException(f"Email '{payload.email}' is already registered.")
        if await self.repository.get_by_contact_no(payload.contact_no):
            raise ConflictException(f"Contact number '{payload.contact_no}' is already registered.")
        if not await self.role_repository.get_by_id(payload.role_id):
            raise BadRequestException(f"Role '{payload.role_id}' does not exist.")
        if payload.company_id and not await self.company_repository.get_by_id(payload.company_id):
            raise BadRequestException(f"Company '{payload.company_id}' does not exist.")

        user = User(
            email=payload.email,
            contact_no=payload.contact_no,
            first_name=payload.first_name,
            middle_name=payload.middle_name,
            last_name=payload.last_name,
            dob=payload.dob,
            hashed_password=hash_password(payload.password),
            address_line_1=payload.address_line_1,
            address_line_2=payload.address_line_2,
            city=payload.city,
            state=payload.state,
            country=payload.country,
            pincode=payload.pincode,
            role_id=payload.role_id,
            company_id=payload.company_id,
        )
        user = await self.repository.create(user)
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: uuid.UUID, payload: UserUpdate) -> UserResponse:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundException("User", str(user_id))

        update_data = payload.model_dump(exclude_unset=True)

        if "role_id" in update_data and not await self.role_repository.get_by_id(update_data["role_id"]):
            raise BadRequestException(f"Role '{update_data['role_id']}' does not exist.")
        if "company_id" in update_data and update_data["company_id"] and \
                not await self.company_repository.get_by_id(update_data["company_id"]):
            raise BadRequestException(f"Company '{update_data['company_id']}' does not exist.")

        for field, value in update_data.items():
            setattr(user, field, value)

        user = await self.repository.update(user)
        return UserResponse.model_validate(user)

    async def list_user_projects(self, user_id: uuid.UUID, page: int, size: int) -> PaginatedResponse[ProjectResponse]:
        if not await self.repository.get_by_id(user_id):
            raise NotFoundException("User", str(user_id))
        skip = (page - 1) * size
        items, total = await self.project_repository.get_projects_by_user(user_id, skip=skip, limit=size)
        return PaginatedResponse(
            items=[ProjectResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundException("User", str(user_id))
        await self.repository.delete(user)

    # ── JIRA User Sync ───────────────────────────────────────────────────────

    async def _get_jira_project_key(self, project_id: uuid.UUID) -> str:
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        if not project.jira_project_key:
            raise BadRequestException("This project has no JIRA project key configured.")
        return project.jira_project_key

    async def preview_jira_users(self, project_id: uuid.UUID) -> list[JiraUserPreview]:
        from app.services.jira_service import JiraService

        jira_project_key = await self._get_jira_project_key(project_id)
        jira = JiraService()
        jira_users = await jira.fetch_project_members(jira_project_key)

        emails = [u.email for u in jira_users if u.email]
        local_by_email = {u.email: u for u in await self.repository.get_by_emails(emails)}

        previews: list[JiraUserPreview] = []
        for ju in jira_users:
            local = local_by_email.get(ju.email) if ju.email else None
            if local and local.jira_account_id == ju.account_id:
                match_status = "already_linked"
                local_user_id = local.id
            elif local:
                match_status = "email_match"
                local_user_id = local.id
            else:
                match_status = "new"
                local_user_id = None
            previews.append(JiraUserPreview(
                account_id=ju.account_id,
                display_name=ju.display_name,
                email=ju.email,
                avatar_url=ju.avatar_url,
                active=ju.active,
                match_status=match_status,
                local_user_id=local_user_id,
            ))
        return previews

    async def sync_users_from_jira(self, payload: JiraUserSyncRequest) -> JiraUserSyncResult:
        import secrets
        from app.services.jira_service import JiraService

        jira_project_key = await self._get_jira_project_key(payload.project_id)

        if not await self.role_repository.get_by_id(payload.role_id):
            raise BadRequestException(f"Role '{payload.role_id}' does not exist.")

        jira = JiraService()
        jira_users = await jira.fetch_project_members(jira_project_key)
        jira_map = {ju.account_id: ju for ju in jira_users}

        selected = [jira_map[aid] for aid in payload.account_ids if aid in jira_map]

        emails = [ju.email for ju in selected if ju.email]
        local_by_email = {u.email: u for u in await self.repository.get_by_emails(emails)}

        linked: list[UserResponse] = []
        created: list[UserResponse] = []
        failed: list[JiraUserSyncFailure] = []

        for ju in selected:
            try:
                local = local_by_email.get(ju.email) if ju.email else None
                if local:
                    local.jira_account_id = ju.account_id
                    user = await self.repository.update(local)
                    linked.append(UserResponse.model_validate(user))
                else:
                    contact_placeholder = f"JIRA-{ju.account_id}"[:50]
                    if await self.repository.get_by_contact_no(contact_placeholder):
                        contact_placeholder = f"J-{ju.account_id}"[:50]
                    name_parts = ju.display_name.split(" ", 1)
                    first_name = name_parts[0] if name_parts else None
                    last_name = name_parts[1] if len(name_parts) > 1 else None
                    new_user = User(
                        email=ju.email or f"{ju.account_id}@jira.local",
                        contact_no=contact_placeholder,
                        first_name=first_name,
                        last_name=last_name,
                        hashed_password=hash_password(secrets.token_urlsafe(16)),
                        jira_account_id=ju.account_id,
                        role_id=payload.role_id,
                    )
                    user = await self.repository.create(new_user)
                    created.append(UserResponse.model_validate(user))
            except Exception as exc:
                failed.append(JiraUserSyncFailure(
                    account_id=ju.account_id,
                    display_name=ju.display_name,
                    error=str(exc),
                ))

        return JiraUserSyncResult(linked=linked, created=created, failed=failed)
