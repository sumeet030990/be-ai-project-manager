"""rename modules to features

Revision ID: n5o6p7q8r9s0
Revises: m4n5o6p7q8r9
Create Date: 2026-06-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "n5o6p7q8r9s0"
down_revision: Union[str, None] = "m4n5o6p7q8r9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("modules", "features")

    op.drop_index("ix_modules_project_id", table_name="features")
    op.drop_index("ix_modules_status", table_name="features")
    op.create_index("ix_features_project_id", "features", ["project_id"])
    op.create_index("ix_features_status", "features", ["status"])

    op.alter_column("stories", "module_id", new_column_name="feature_id")

    op.drop_index("ix_stories_module_id", table_name="stories")
    op.create_index("ix_stories_feature_id", "stories", ["feature_id"])

    op.drop_constraint("stories_module_id_fkey", "stories", type_="foreignkey")
    op.create_foreign_key(
        "stories_feature_id_fkey",
        "stories",
        "features",
        ["feature_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("stories_feature_id_fkey", "stories", type_="foreignkey")
    op.create_foreign_key(
        "stories_module_id_fkey",
        "stories",
        "modules",
        ["feature_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_index("ix_stories_feature_id", table_name="stories")
    op.create_index("ix_stories_module_id", "stories", ["feature_id"])
    op.alter_column("stories", "feature_id", new_column_name="module_id")

    op.drop_index("ix_features_project_id", table_name="features")
    op.drop_index("ix_features_status", table_name="features")
    op.create_index("ix_modules_project_id", "features", ["project_id"])
    op.create_index("ix_modules_status", "features", ["status"])

    op.rename_table("features", "modules")
