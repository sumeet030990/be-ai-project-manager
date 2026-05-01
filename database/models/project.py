from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.company import Company
    from database.models.user import User
    from database.models.project_user import ProjectUser


class Project(BaseModel):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    company: Mapped["Company"] = relationship("Company", lazy="noload")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by], lazy="noload")
    project_users: Mapped[list["ProjectUser"]] = relationship("ProjectUser", back_populates="project", lazy="noload")

    __table_args__ = (
        Index("ix_projects_name", "name"),
        Index("ix_projects_company_id", "company_id"),
        Index("ix_projects_status", "status"),
    )
