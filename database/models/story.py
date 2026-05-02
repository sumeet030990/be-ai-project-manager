from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.module import Module


class Story(BaseModel):
    __tablename__ = "stories"

    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    azure_work_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    business_rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_references: Mapped[str | None] = mapped_column(Text, nullable=True)
    urls: Mapped[str | None] = mapped_column(Text, nullable=True)

    module: Mapped["Module | None"] = relationship("Module", back_populates="stories", lazy="noload")

    __table_args__ = (
        Index("ix_stories_module_id", "module_id"),
        Index("ix_stories_status", "status"),
    )
