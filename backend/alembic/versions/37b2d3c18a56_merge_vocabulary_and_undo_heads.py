"""merge vocabulary and undo heads

Revision ID: 37b2d3c18a56
Revises: 3a8f6e5d9c12, 9f2d4b7c6a11
Create Date: 2026-05-07 01:46:12.987847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37b2d3c18a56'
down_revision: Union[str, Sequence[str], None] = ('3a8f6e5d9c12', '9f2d4b7c6a11')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
