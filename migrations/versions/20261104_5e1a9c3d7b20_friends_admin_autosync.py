"""friends, last seen and automatic syncs

Revision ID: 5e1a9c3d7b20
Revises: 2bf08fe8de93
Create Date: 2026-11-04 09:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5e1a9c3d7b20"
down_revision: str | None = "2bf08fe8de93"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

friendship_status = postgresql.ENUM("pending", "accepted", name="friendship_status")


def upgrade() -> None:
    friendship_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "friendships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("addressee_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(name="friendship_status", create_type=False),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("requester_id <> addressee_id", name=op.f("ck_friendships_not_self")),
        sa.ForeignKeyConstraint(
            ["addressee_id"],
            ["users.id"],
            name=op.f("fk_friendships_addressee_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requester_id"],
            ["users.id"],
            name=op.f("fk_friendships_requester_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_friendships")),
        sa.UniqueConstraint(
            "requester_id", "addressee_id", name=op.f("uq_friendships_requester_id")
        ),
    )
    op.create_index(
        op.f("ix_friendships_addressee_id"), "friendships", ["addressee_id"], unique=False
    )
    op.add_column("users", sa.Column("last_seen_at", sa.DateTime(), nullable=True))
    op.add_column(
        "sync_jobs",
        sa.Column("automatic", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("sync_jobs", "automatic")
    op.drop_column("users", "last_seen_at")
    op.drop_index(op.f("ix_friendships_addressee_id"), table_name="friendships")
    op.drop_table("friendships")
    friendship_status.drop(op.get_bind(), checkfirst=True)
