from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.project import Project
    from database.models.sprint_story import SprintStory


class Sprint(BaseModel):
    __tablename__ = "sprints"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="planning", nullable=False)
    jira_sprint_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    project: Mapped["Project"] = relationship("Project", lazy="noload")
    sprint_stories: Mapped[list["SprintStory"]] = relationship(
        "SprintStory", back_populates="sprint", lazy="noload", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_sprints_project_id", "project_id"),
        Index("ix_sprints_status", "status"),
    )
