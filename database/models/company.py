from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.user import User


class Company(BaseModel):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    gst_no: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="company", lazy="noload")

    __table_args__ = (
        Index("ix_companies_name", "name"),
        Index("ix_companies_gst_no", "gst_no"),
    )
