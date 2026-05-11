from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.story import Story


class TestCase(BaseModel):
    __tablename__ = "test_cases"

    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_type: Mapped[str] = mapped_column(String(20), default="positive", nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    story: Mapped["Story | None"] = relationship("Story", back_populates="test_cases", lazy="noload")

    __table_args__ = (
        Index("ix_test_cases_story_id", "story_id"),
        Index("ix_test_cases_test_type", "test_type"),
    )
