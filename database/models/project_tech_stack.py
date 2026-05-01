from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.project import Project
    from database.models.project_plugin import ProjectPlugin


class ProjectTechStack(BaseModel):
    __tablename__ = "project_tech_stacks"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="tech_stacks", lazy="noload")
    plugins: Mapped[list["ProjectPlugin"]] = relationship("ProjectPlugin", back_populates="tech_stack", lazy="noload")

    __table_args__ = (
        Index("ix_project_tech_stacks_project_id", "project_id"),
        Index("ix_project_tech_stacks_category", "category"),
    )
