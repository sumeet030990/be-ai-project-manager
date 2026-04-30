import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    gst_no: str | None = Field(default=None, max_length=20)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=50)
    website: str | None = Field(default=None, max_length=255)
    address_line_1: str = Field(..., min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    pincode: str = Field(..., min_length=1, max_length=20)


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    gst_no: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=7, max_length=50)
    website: str | None = Field(default=None, max_length=255)
    address_line_1: str | None = Field(default=None, min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    pincode: str | None = Field(default=None, min_length=1, max_length=20)
    is_active: bool | None = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    gst_no: str | None
    email: str
    phone: str
    website: str | None
    address_line_1: str
    address_line_2: str | None
    city: str
    state: str
    country: str
    pincode: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
