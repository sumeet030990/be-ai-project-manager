import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.company import CompanyResponse
from app.schemas.role import RoleResponse


class UserCreate(BaseModel):
    email: EmailStr
    contact_no: str = Field(..., min_length=7, max_length=50)
    first_name: str | None = Field(default=None, max_length=255)
    middle_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    dob: date | None = None
    password: str = Field(..., min_length=8)
    address_line_1: str | None = Field(default=None, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=20)
    role_id: uuid.UUID
    company_id: uuid.UUID | None = None


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=255)
    middle_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    dob: date | None = None
    is_active: bool | None = None
    address_line_1: str | None = Field(default=None, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=20)
    role_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    contact_no: str
    first_name: str | None
    middle_name: str | None
    last_name: str | None
    dob: date | None
    is_active: bool
    address_line_1: str | None
    address_line_2: str | None
    city: str | None
    state: str | None
    country: str | None
    pincode: str | None
    role_id: uuid.UUID
    role: RoleResponse
    company_id: uuid.UUID | None
    company: CompanyResponse | None
    jira_account_id: str | None
    created_at: datetime
    updated_at: datetime


JiraMatchStatus = Literal["already_linked", "email_match", "new"]


class JiraUserPreview(BaseModel):
    account_id: str
    display_name: str
    email: str | None
    avatar_url: str | None
    active: bool
    match_status: JiraMatchStatus
    local_user_id: uuid.UUID | None


class JiraUserSyncRequest(BaseModel):
    project_id: uuid.UUID
    account_ids: list[str]
    role_id: uuid.UUID


class JiraUserSyncFailure(BaseModel):
    account_id: str
    display_name: str
    error: str


class JiraUserSyncResult(BaseModel):
    linked: list[UserResponse]
    created: list[UserResponse]
    failed: list[JiraUserSyncFailure]
