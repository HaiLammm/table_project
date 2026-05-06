"""add vocabulary tables

Revision ID: 9f2d4b7c6a11
Revises: 5c2e3a4f9b11
Create Date: 2026-05-06 00:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9f2d4b7c6a11"
down_revision: Union[str, Sequence[str], None] = "5c2e3a4f9b11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "vocabulary_terms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("term", sa.String(length=500), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("cefr_level", sa.String(length=5), nullable=True),
        sa.Column("jlpt_level", sa.String(length=5), nullable=True),
        sa.Column("part_of_speech", sa.String(length=30), nullable=True),
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
        sa.CheckConstraint(
            "language IN ('en', 'jp')",
            name="ck_vocabulary_terms_language",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["vocabulary_terms.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("term", "language", name="uq_vocabulary_terms_term_language"),
    )
    op.create_index(
        "ix_vocabulary_terms_parent_id",
        "vocabulary_terms",
        ["parent_id"],
        unique=False,
    )
    op.create_index(
        "ix_vocabulary_terms_language",
        "vocabulary_terms",
        ["language"],
        unique=False,
    )
    op.execute(
        "CREATE INDEX ix_vocabulary_terms_search "
        "ON vocabulary_terms USING GIN (to_tsvector('simple', term))",
    )

    op.create_table(
        "vocabulary_definitions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("term_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("ipa", sa.String(length=255), nullable=True),
        sa.Column(
            "examples",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column(
            "validated_against_jmdict",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "source IN ('seed', 'user', 'llm')",
            name="ck_vocabulary_definitions_source",
        ),
        sa.CheckConstraint(
            "language IN ('en', 'jp')",
            name="ck_vocabulary_definitions_language",
        ),
        sa.ForeignKeyConstraint(["term_id"], ["vocabulary_terms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vocabulary_definitions_term_id",
        "vocabulary_definitions",
        ["term_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_vocabulary_definitions_term_id", table_name="vocabulary_definitions")
    op.drop_table("vocabulary_definitions")
    op.execute("DROP INDEX IF EXISTS ix_vocabulary_terms_search")
    op.drop_index("ix_vocabulary_terms_language", table_name="vocabulary_terms")
    op.drop_index("ix_vocabulary_terms_parent_id", table_name="vocabulary_terms")
    op.drop_table("vocabulary_terms")
