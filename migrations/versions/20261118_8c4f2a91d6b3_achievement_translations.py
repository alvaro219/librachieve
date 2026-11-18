"""achievement names and descriptions per language

Revision ID: 8c4f2a91d6b3
Revises: 5e1a9c3d7b20
Create Date: 2026-11-18 09:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8c4f2a91d6b3"
down_revision: str | None = "5e1a9c3d7b20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "achievements",
        sa.Column(
            "localized",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    # Until now the schema was downloaded in Spanish: keep it as the Spanish text. The next
    # Steam sync downloads every language again (new cache key) and sets the English base.
    op.execute(
        """
        UPDATE achievements
        SET localized = jsonb_build_object(
            'es', jsonb_build_object('name', name, 'description', description)
        )
        """
    )


def downgrade() -> None:
    op.drop_column("achievements", "localized")
