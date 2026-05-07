"""add undo support to srs reviews

Revision ID: 3a8f6e5d9c12
Revises: 2e7d2c4c9f10
Create Date: 2026-05-07 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "3a8f6e5d9c12"
down_revision: Union[str, Sequence[str], None] = "2e7d2c4c9f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "srs_reviews",
        sa.Column("previous_fsrs_state", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "srs_reviews",
        sa.Column("previous_stability", sa.Float(), nullable=True),
    )
    op.add_column(
        "srs_reviews",
        sa.Column("previous_difficulty", sa.Float(), nullable=True),
    )
    op.add_column(
        "srs_reviews",
        sa.Column("previous_reps", sa.Integer(), nullable=True),
    )
    op.add_column(
        "srs_reviews",
        sa.Column("previous_lapses", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("srs_reviews", "previous_lapses")
    op.drop_column("srs_reviews", "previous_reps")
    op.drop_column("srs_reviews", "previous_difficulty")
    op.drop_column("srs_reviews", "previous_stability")
    op.drop_column("srs_reviews", "previous_fsrs_state")
