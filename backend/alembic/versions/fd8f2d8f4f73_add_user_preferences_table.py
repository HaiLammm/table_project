"""add user preferences table

Revision ID: fd8f2d8f4f73
Revises: 1cc5f6af6b47
Create Date: 2026-05-06 00:00:01.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fd8f2d8f4f73"
down_revision: Union[str, Sequence[str], None] = "1cc5f6af6b47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("learning_goal", sa.String(length=50), nullable=False),
        sa.Column("english_level", sa.String(length=20), nullable=False),
        sa.Column("japanese_level", sa.String(length=10), nullable=False),
        sa.Column("daily_study_minutes", sa.Integer(), server_default="15", nullable=False),
        sa.Column("it_domain", sa.String(length=30), server_default="general_it", nullable=False),
        sa.Column(
            "notification_email", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "notification_review_reminder",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_table("user_preferences")
