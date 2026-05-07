"""create diagnostic insights tables

Revision ID: 8b2c4d6e7f80
Revises: fa8a61335426
Create Date: 2026-05-07 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8b2c4d6e7f80"
down_revision: Union[str, Sequence[str], None] = "fa8a61335426"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "diagnostic_insights",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("icon", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("action_label", sa.String(length=100), nullable=True),
        sa.Column("action_href", sa.String(length=200), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "severity IN ('info', 'warning', 'success')",
            name="chk_diagnostic_insights_severity",
        ),
        sa.CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="chk_diagnostic_insights_confidence",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_diagnostic_insights_user_created",
        "diagnostic_insights",
        ["user_id", sa.text("created_at DESC")],
        unique=False,
    )

    op.create_table(
        "insight_seen",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("insight_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["insight_id"], ["diagnostic_insights.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("insight_id", "user_id", "session_id", name="uq_insight_seen"),
    )
    op.create_index(
        "ix_insight_seen_user_session",
        "insight_seen",
        ["user_id", "session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_insight_seen_user_session", table_name="insight_seen")
    op.drop_table("insight_seen")
    op.drop_index("ix_diagnostic_insights_user_created", table_name="diagnostic_insights")
    op.drop_table("diagnostic_insights")
