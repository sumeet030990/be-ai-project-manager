from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.project import Project
    from database.models.user import User


class ProjectUser(BaseModel):
    __tablename__ = "project_users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship("User", lazy="noload")
    project: Mapped["Project"] = relationship("Project", back_populates="project_users", lazy="noload")

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_project_users_user_project"),
        Index("ix_project_users_user_id", "user_id"),
        Index("ix_project_users_project_id", "project_id"),
    )
