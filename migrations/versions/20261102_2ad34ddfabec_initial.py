"""initial

Revision ID: 2ad34ddfabec
Revises:
Create Date: 2026-11-02 09:15:48.135127+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "2ad34ddfabec"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Shared Postgres enum types are created/dropped explicitly (platform is used by two tables).
user_role = postgresql.ENUM("user", "admin", name="user_role", create_type=False)
platform = postgresql.ENUM(
    "steam", "epic", "gog", "amazon", "other", name="platform", create_type=False
)
game_status = postgresql.ENUM(
    "backlog",
    "playing",
    "completed",
    "dropped",
    "wishlist",
    "other",
    name="game_status",
    create_type=False,
)
sync_job_status = postgresql.ENUM(
    "pending", "running", "success", "failed", name="sync_job_status", create_type=False
)
ENUMS = (user_role, platform, game_status, sync_job_status)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in ENUMS:
        enum.create(bind, checkfirst=True)

    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("normalized_title", sa.String(length=255), nullable=False),
        sa.Column("igdb_id", sa.Integer(), nullable=True),
        sa.Column("steam_appid", sa.Integer(), nullable=True),
        sa.Column("cover_url", sa.String(length=512), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column(
            "genres", postgresql.ARRAY(sa.String(length=64)), server_default="{}", nullable=False
        ),
        sa.Column("metadata_updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_games")),
        sa.UniqueConstraint("igdb_id", name=op.f("uq_games_igdb_id")),
        sa.UniqueConstraint("steam_appid", name=op.f("uq_games_steam_appid")),
    )
    op.create_index(op.f("ix_games_normalized_title"), "games", ["normalized_title"], unique=False)
    op.create_index(op.f("ix_games_title"), "games", ["title"], unique=False)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("steam_id", sa.String(length=32), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("role", user_role, server_default="user", nullable=False),
        sa.Column("is_public", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        sa.UniqueConstraint("steam_id", name=op.f("uq_users_steam_id")),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_table(
        "library_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("platform", platform, nullable=False),
        sa.Column("status", game_status, server_default="backlog", nullable=False),
        sa.Column("custom_folder", sa.String(length=64), nullable=True),
        sa.Column("playtime_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_played_at", sa.DateTime(), nullable=True),
        sa.Column("added_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
            name=op.f("fk_library_entries_game_id_games"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_library_entries_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_library_entries")),
        sa.UniqueConstraint(
            "user_id", "game_id", "platform", name=op.f("uq_library_entries_user_id")
        ),
    )
    op.create_index(
        op.f("ix_library_entries_game_id"), "library_entries", ["game_id"], unique=False
    )
    op.create_index(op.f("ix_library_entries_status"), "library_entries", ["status"], unique=False)
    op.create_index(
        op.f("ix_library_entries_user_id"), "library_entries", ["user_id"], unique=False
    )
    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("platform", platform, nullable=False),
        sa.Column("status", sync_job_status, server_default="pending", nullable=False),
        sa.Column("imported_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_sync_jobs_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sync_jobs")),
    )
    op.create_index(op.f("ix_sync_jobs_user_id"), "sync_jobs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sync_jobs_user_id"), table_name="sync_jobs")
    op.drop_table("sync_jobs")
    op.drop_index(op.f("ix_library_entries_user_id"), table_name="library_entries")
    op.drop_index(op.f("ix_library_entries_status"), table_name="library_entries")
    op.drop_index(op.f("ix_library_entries_game_id"), table_name="library_entries")
    op.drop_table("library_entries")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_games_title"), table_name="games")
    op.drop_index(op.f("ix_games_normalized_title"), table_name="games")
    op.drop_table("games")

    bind = op.get_bind()
    for enum in ENUMS:
        enum.drop(bind, checkfirst=True)
