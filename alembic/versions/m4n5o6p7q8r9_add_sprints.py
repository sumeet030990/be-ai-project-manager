"""add sprints

Revision ID: m4n5o6p7q8r9
Revises: l3m4n5o6p7q8
Create Date: 2026-05-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "m4n5o6p7q8r9"
down_revision: Union[str, None] = "l3m4n5o6p7q8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("jira_board_id", sa.Integer(), nullable=True))

    op.create_table(
        "sprints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="planning"),
        sa.Column("jira_sprint_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sprints_project_id", "sprints", ["project_id"])
    op.create_index("ix_sprints_status", "sprints", ["status"])

    op.create_table(
        "sprint_stories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sprint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("story_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["sprint_id"], ["sprints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sprint_id", "story_id", name="uq_sprint_stories_sprint_story"),
    )
    op.create_index("ix_sprint_stories_sprint_id", "sprint_stories", ["sprint_id"])
    op.create_index("ix_sprint_stories_story_id", "sprint_stories", ["story_id"])


def downgrade() -> None:
    op.drop_index("ix_sprint_stories_story_id", table_name="sprint_stories")
    op.drop_index("ix_sprint_stories_sprint_id", table_name="sprint_stories")
    op.drop_table("sprint_stories")

    op.drop_index("ix_sprints_status", table_name="sprints")
    op.drop_index("ix_sprints_project_id", table_name="sprints")
    op.drop_table("sprints")

    op.drop_column("projects", "jira_board_id")
