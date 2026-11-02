"""library favorites

Revision ID: 38e289b97748
Revises: 1cc677f109f1
Create Date: 2026-11-02 18:26:32.588365+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "38e289b97748"
down_revision: str | None = "1cc677f109f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "library_entries",
        sa.Column("is_favorite", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("library_entries", "is_favorite")
