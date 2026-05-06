"""expand srs cards with fsrs reviews

Revision ID: 2e7d2c4c9f10
Revises: 5c2e3a4f9b11
Create Date: 2026-05-06 14:58:00.000000

"""

import json
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from fsrs import Card
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2e7d2c4c9f10"
down_revision: Union[str, Sequence[str], None] = "5c2e3a4f9b11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _build_legacy_fsrs_state(card_id: int, due_at: datetime) -> dict[str, object]:
    normalized_due_at = (
        due_at.astimezone(UTC) if due_at.tzinfo is not None else due_at.replace(tzinfo=UTC)
    )
    return json.loads(Card(card_id=card_id, due=normalized_due_at).to_json())


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "srs_cards",
        sa.Column(
            "language",
            sa.String(length=5),
            server_default=sa.text("'en'"),
            nullable=False,
        ),
    )
    op.add_column("srs_cards", sa.Column("stability", sa.Float(), nullable=True))
    op.add_column("srs_cards", sa.Column("difficulty", sa.Float(), nullable=True))
    op.add_column(
        "srs_cards",
        sa.Column("reps", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "srs_cards",
        sa.Column("lapses", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.create_check_constraint(
        "ck_srs_cards_language",
        "srs_cards",
        "language IN ('en', 'jp')",
    )
    op.create_unique_constraint(
        "uq_srs_cards_user_id_term_id_language",
        "srs_cards",
        ["user_id", "term_id", "language"],
    )

    connection = op.get_bind()
    srs_cards_table = sa.table(
        "srs_cards",
        sa.column("id", sa.Integer()),
        sa.column("due_at", sa.DateTime(timezone=True)),
        sa.column("fsrs_state", postgresql.JSONB(astext_type=sa.Text())),
    )
    existing_cards = connection.execute(
        sa.select(
            srs_cards_table.c.id,
            srs_cards_table.c.due_at,
            srs_cards_table.c.fsrs_state,
        )
    ).mappings()
    for existing_card in existing_cards:
        fsrs_state = existing_card["fsrs_state"]
        if fsrs_state and all(key in fsrs_state for key in ("card_id", "state", "due")):
            continue

        connection.execute(
            sa.update(srs_cards_table)
            .where(srs_cards_table.c.id == existing_card["id"])
            .values(
                fsrs_state=_build_legacy_fsrs_state(existing_card["id"], existing_card["due_at"])
            ),
        )

    op.create_table(
        "srs_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("rating BETWEEN 1 AND 4", name="ck_srs_reviews_rating"),
        sa.ForeignKeyConstraint(["card_id"], ["srs_cards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_srs_reviews_card_id", "srs_reviews", ["card_id"], unique=False)
    op.create_index("ix_srs_reviews_user_id", "srs_reviews", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_srs_reviews_user_id", table_name="srs_reviews")
    op.drop_index("ix_srs_reviews_card_id", table_name="srs_reviews")
    op.drop_table("srs_reviews")
    op.drop_constraint("uq_srs_cards_user_id_term_id_language", "srs_cards", type_="unique")
    op.drop_constraint("ck_srs_cards_language", "srs_cards", type_="check")
    op.drop_column("srs_cards", "lapses")
    op.drop_column("srs_cards", "reps")
    op.drop_column("srs_cards", "difficulty")
    op.drop_column("srs_cards", "stability")
    op.drop_column("srs_cards", "language")
