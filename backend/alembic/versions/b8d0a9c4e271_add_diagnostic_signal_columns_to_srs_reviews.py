"""add diagnostic signal columns to srs reviews

Revision ID: b8d0a9c4e271
Revises: 8b2c4d6e7f80
Create Date: 2026-05-07 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b8d0a9c4e271"
down_revision: str | Sequence[str] | None = "8b2c4d6e7f80"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "srs_reviews",
        sa.Column("session_length_s", sa.Integer(), nullable=True),
    )
    op.add_column(
        "srs_reviews",
        sa.Column(
            "parallel_mode_active",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_srs_reviews_user_reviewed",
        "srs_reviews",
        ["user_id", "reviewed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_srs_reviews_user_reviewed", table_name="srs_reviews")
    op.drop_column("srs_reviews", "parallel_mode_active")
    op.drop_column("srs_reviews", "session_length_s")
