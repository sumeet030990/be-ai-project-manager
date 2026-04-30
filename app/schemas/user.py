import uuid
from datetime import date, datetime

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
    created_at: datetime
    updated_at: datetime
