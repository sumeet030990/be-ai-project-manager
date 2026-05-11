"""add test_cases table

Revision ID: c4d5e6f7g8h9
Revises: a2b3c4d5e6f7
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c4d5e6f7g8h9"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "test_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("story_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("steps", sa.Text(), nullable=True),
        sa.Column("expected_result", sa.Text(), nullable=True),
        sa.Column("test_type", sa.String(length=20), nullable=False, server_default="positive"),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_ai_generated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_test_cases_story_id", "test_cases", ["story_id"], unique=False)
    op.create_index("ix_test_cases_test_type", "test_cases", ["test_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_test_cases_test_type", table_name="test_cases")
    op.drop_index("ix_test_cases_story_id", table_name="test_cases")
    op.drop_table("test_cases")
