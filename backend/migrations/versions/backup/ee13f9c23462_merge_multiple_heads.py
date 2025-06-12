"""Merge multiple heads

Revision ID: ee13f9c23462
Revises: bb57dd13ac87
Create Date: 2025-06-09 15:34:46.225686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee13f9c23462'
down_revision: Union[str, None] = 'bb57dd13ac87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
