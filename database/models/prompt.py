from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.story import Story


class Prompt(BaseModel):
    __tablename__ = "prompts"

    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    target_ai: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    tech_stacks: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    story: Mapped["Story | None"] = relationship("Story", lazy="noload")

    __table_args__ = (Index("ix_prompts_story_id", "story_id"),)
