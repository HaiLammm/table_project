"""add data exports table

Revision ID: 7b1d5f4c2a10
Revises: fd8f2d8f4f73
Create Date: 2026-05-06 00:00:02.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b1d5f4c2a10"
down_revision: Union[str, Sequence[str], None] = "fd8f2d8f4f73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "data_exports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_exports_status", "data_exports", ["status"], unique=False)
    op.create_index("ix_data_exports_user_id", "data_exports", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_data_exports_user_id", table_name="data_exports")
    op.drop_index("ix_data_exports_status", table_name="data_exports")
    op.drop_table("data_exports")
