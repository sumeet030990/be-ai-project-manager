"""add project_tech_stacks and project_plugins

Revision ID: a1b2c3d4e5f6
Revises: 72a2d8213aba
Create Date: 2026-05-01 20:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "72a2d8213aba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_tech_stacks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(100), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_project_tech_stacks_project_id", "project_tech_stacks", ["project_id"])
    op.create_index("ix_project_tech_stacks_category", "project_tech_stacks", ["category"])

    op.create_table(
        "project_plugins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tech_stack_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_tech_stacks.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(100), nullable=True),
        sa.Column("ecosystem", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_project_plugins_project_id", "project_plugins", ["project_id"])
    op.create_index("ix_project_plugins_tech_stack_id", "project_plugins", ["tech_stack_id"])
    op.create_index("ix_project_plugins_ecosystem", "project_plugins", ["ecosystem"])


def downgrade() -> None:
    op.drop_index("ix_project_plugins_ecosystem", table_name="project_plugins")
    op.drop_index("ix_project_plugins_tech_stack_id", table_name="project_plugins")
    op.drop_index("ix_project_plugins_project_id", table_name="project_plugins")
    op.drop_table("project_plugins")

    op.drop_index("ix_project_tech_stacks_category", table_name="project_tech_stacks")
    op.drop_index("ix_project_tech_stacks_project_id", table_name="project_tech_stacks")
    op.drop_table("project_tech_stacks")
