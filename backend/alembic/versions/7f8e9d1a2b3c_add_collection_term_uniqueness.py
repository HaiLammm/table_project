"""add collection term uniqueness

Revision ID: 7f8e9d1a2b3c
Revises: c2f7a9d4b6e1
Create Date: 2026-05-07 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "7f8e9d1a2b3c"
down_revision: Union[str, Sequence[str], None] = "c2f7a9d4b6e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_collection_terms_collection_id_term_id",
        "collection_terms",
        ["collection_id", "term_id"],
    )
    op.create_index(
        "ix_collection_terms_term_id",
        "collection_terms",
        ["term_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_collection_terms_term_id", table_name="collection_terms")
    op.drop_constraint(
        "uq_collection_terms_collection_id_term_id",
        "collection_terms",
        type_="unique",
    )
