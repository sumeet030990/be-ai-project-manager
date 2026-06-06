"""add ai fields to features

Revision ID: p7q8r9s0t1u2
Revises: o6p7q8r9s0t1
Create Date: 2026-06-06

"""
from alembic import op
import sqlalchemy as sa

revision = "p7q8r9s0t1u2"
down_revision = "o6p7q8r9s0t1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("features", sa.Column("is_ai_generated", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("features", sa.Column("business_rules", sa.Text(), nullable=True))
    op.add_column("features", sa.Column("acceptance_criteria", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("features", "acceptance_criteria")
    op.drop_column("features", "business_rules")
    op.drop_column("features", "is_ai_generated")
