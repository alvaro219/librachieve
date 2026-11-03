"""game ratings

Revision ID: 2bf08fe8de93
Revises: 7ad6fecd9845
Create Date: 2026-11-03 09:26:56.322078+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2bf08fe8de93"
down_revision: str | None = "7ad6fecd9845"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "game_ratings",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name=op.f("ck_game_ratings_score_range")),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
            name=op.f("fk_game_ratings_game_id_games"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_game_ratings_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "game_id", name=op.f("pk_game_ratings")),
    )
    op.create_index(op.f("ix_game_ratings_game_id"), "game_ratings", ["game_id"], unique=False)
    op.add_column("games", sa.Column("igdb_rating", sa.Float(), nullable=True))
    op.add_column("games", sa.Column("igdb_rating_count", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("critic_rating", sa.Float(), nullable=True))
    op.add_column("games", sa.Column("critic_rating_count", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("community_rating", sa.Float(), nullable=True))
    op.add_column(
        "games",
        sa.Column("community_rating_count", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("games", "community_rating_count")
    op.drop_column("games", "community_rating")
    op.drop_column("games", "critic_rating_count")
    op.drop_column("games", "critic_rating")
    op.drop_column("games", "igdb_rating_count")
    op.drop_column("games", "igdb_rating")
    op.drop_index(op.f("ix_game_ratings_game_id"), table_name="game_ratings")
    op.drop_table("game_ratings")
