from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.project import Project
    from database.models.project_tech_stack import ProjectTechStack


class ProjectPlugin(BaseModel):
    __tablename__ = "project_plugins"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    tech_stack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_tech_stacks.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ecosystem: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="plugins", lazy="noload")
    tech_stack: Mapped["ProjectTechStack"] = relationship("ProjectTechStack", back_populates="plugins", lazy="noload")

    __table_args__ = (
        Index("ix_project_plugins_project_id", "project_id"),
        Index("ix_project_plugins_tech_stack_id", "tech_stack_id"),
        Index("ix_project_plugins_ecosystem", "ecosystem"),
    )
