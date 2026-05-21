from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.sprint import Sprint
    from database.models.story import Story


class SprintStory(BaseModel):
    __tablename__ = "sprint_stories"

    sprint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False
    )
    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
    )

    sprint: Mapped["Sprint"] = relationship("Sprint", back_populates="sprint_stories", lazy="noload")
    story: Mapped["Story"] = relationship("Story", lazy="noload")

    __table_args__ = (
        UniqueConstraint("sprint_id", "story_id", name="uq_sprint_stories_sprint_story"),
    )
