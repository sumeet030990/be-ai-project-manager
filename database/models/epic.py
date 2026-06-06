from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.project import Project
    from database.models.feature import Feature


class Epic(BaseModel):
    __tablename__ = "epics"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jira_epic_key: Mapped[str | None] = mapped_column(String(50), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="epics", lazy="noload")
    features: Mapped[list["Feature"]] = relationship("Feature", back_populates="epic", lazy="noload")

    __table_args__ = (
        Index("ix_epics_project_id", "project_id"),
        Index("ix_epics_status", "status"),
    )
