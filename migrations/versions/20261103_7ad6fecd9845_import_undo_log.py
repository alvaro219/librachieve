"""import undo log

Revision ID: 7ad6fecd9845
Revises: 38e289b97748
Create Date: 2026-11-03 08:49:41.654462+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7ad6fecd9845"
down_revision: str | None = "38e289b97748"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Existing enum type, reused (created by the initial migration)
game_status = postgresql.ENUM(name="game_status", create_type=False)


def upgrade() -> None:
    op.execute("ALTER TYPE sync_job_status ADD VALUE IF NOT EXISTS 'reverted'")
    op.create_table(
        "sync_job_changes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("created", sa.Boolean(), nullable=False),
        sa.Column("prev_status", game_status, nullable=True),
        sa.Column("prev_playtime_minutes", sa.Integer(), nullable=True),
        sa.Column("prev_last_played_at", sa.DateTime(), nullable=True),
        sa.Column("prev_is_favorite", sa.Boolean(), nullable=True),
        sa.Column("prev_custom_folder", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["sync_jobs.id"],
            name=op.f("fk_sync_job_changes_job_id_sync_jobs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sync_job_changes")),
    )
    op.create_index(
        op.f("ix_sync_job_changes_job_id"), "sync_job_changes", ["job_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_sync_job_changes_job_id"), table_name="sync_job_changes")
    op.drop_table("sync_job_changes")
    # Postgres cannot drop an enum value; move reverted jobs back and leave the value unused.
    op.execute("UPDATE sync_jobs SET status = 'success' WHERE status = 'reverted'")
