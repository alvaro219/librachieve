"""achievements

Revision ID: 1cc677f109f1
Revises: 2ad34ddfabec
Create Date: 2026-11-02 10:47:52.686263+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "1cc677f109f1"
down_revision: str | None = "2ad34ddfabec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Reuse the existing enum type created by the initial migration.
platform = postgresql.ENUM(name="platform", create_type=False)


def upgrade() -> None:
    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("platform", platform, nullable=False),
        sa.Column("api_name", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon_url", sa.String(length=512), nullable=True),
        sa.Column("icon_locked_url", sa.String(length=512), nullable=True),
        sa.Column("hidden", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("global_percent", sa.Float(), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
            name=op.f("fk_achievements_game_id_games"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_achievements")),
        sa.UniqueConstraint(
            "game_id", "platform", "api_name", name=op.f("uq_achievements_game_id")
        ),
    )
    op.create_index(op.f("ix_achievements_game_id"), "achievements", ["game_id"], unique=False)
    op.create_table(
        "user_achievements",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("achievement_id", sa.Integer(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["achievement_id"],
            ["achievements.id"],
            name=op.f("fk_user_achievements_achievement_id_achievements"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_achievements_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "achievement_id", name=op.f("pk_user_achievements")),
    )
    op.create_index(
        op.f("ix_user_achievements_achievement_id"),
        "user_achievements",
        ["achievement_id"],
        unique=False,
    )
    op.add_column(
        "library_entries",
        sa.Column("achievements_unlocked", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "library_entries",
        sa.Column("achievements_total", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("library_entries", "achievements_total")
    op.drop_column("library_entries", "achievements_unlocked")
    op.drop_index(op.f("ix_user_achievements_achievement_id"), table_name="user_achievements")
    op.drop_table("user_achievements")
    op.drop_index(op.f("ix_achievements_game_id"), table_name="achievements")
    op.drop_table("achievements")
