from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.feature import Feature
    from database.models.test_case import TestCase
    from database.models.user import User


class Story(BaseModel):
    __tablename__ = "stories"

    feature_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("features.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    story_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    azure_work_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jira_issue_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    business_rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_references: Mapped[str | None] = mapped_column(Text, nullable=True)
    urls: Mapped[str | None] = mapped_column(Text, nullable=True)

    feature: Mapped["Feature | None"] = relationship("Feature", back_populates="stories", lazy="noload")
    assignee: Mapped["User | None"] = relationship("User", foreign_keys="Story.assignee_id", lazy="noload")
    test_cases: Mapped[list["TestCase"]] = relationship("TestCase", back_populates="story", lazy="noload", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_stories_feature_id", "feature_id"),
        Index("ix_stories_status", "status"),
    )
