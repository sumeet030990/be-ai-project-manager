"""add modules and stories

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-02 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("order", sa.Integer, default=0, nullable=False),
        sa.Column("status", sa.String(50), server_default="draft", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_modules_project_id", "modules", ["project_id"])
    op.create_index("ix_modules_status", "modules", ["status"])

    op.create_table(
        "stories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=True),
        sa.Column("parent_story_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("story_type", sa.String(20), server_default="story", nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("order", sa.Integer, default=0, nullable=False),
        sa.Column("status", sa.String(50), server_default="draft", nullable=False),
        sa.Column("is_ai_generated", sa.Boolean, server_default="false", nullable=False),
        sa.Column("azure_work_item_id", sa.Integer, nullable=True),
        sa.Column("business_rules", sa.Text, nullable=True),
        sa.Column("acceptance_criteria", sa.Text, nullable=True),
        sa.Column("file_references", sa.Text, nullable=True),
        sa.Column("urls", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_stories_module_id", "stories", ["module_id"])
    op.create_index("ix_stories_parent_story_id", "stories", ["parent_story_id"])
    op.create_index("ix_stories_story_type", "stories", ["story_type"])
    op.create_index("ix_stories_status", "stories", ["status"])


def downgrade() -> None:
    op.drop_index("ix_stories_status", table_name="stories")
    op.drop_index("ix_stories_story_type", table_name="stories")
    op.drop_index("ix_stories_parent_story_id", table_name="stories")
    op.drop_index("ix_stories_module_id", table_name="stories")
    op.drop_table("stories")

    op.drop_index("ix_modules_status", table_name="modules")
    op.drop_index("ix_modules_project_id", table_name="modules")
    op.drop_table("modules")
