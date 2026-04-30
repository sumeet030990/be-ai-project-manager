from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import BaseModel

if TYPE_CHECKING:
    from database.models.user import User


class Role(BaseModel):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="role", lazy="noload")

    __table_args__ = (
        Index("ix_roles_name", "name"),
        Index("ix_roles_slug", "slug"),
    )
