"""add created_at to tags

Revision ID: add_created_at_to_tags
Revises: add_visualization_fields
Create Date: 2025-06-10 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_created_at_to_tags'
down_revision: Union[str, None] = 'add_visualization_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('tags') as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('tags') as batch_op:
        batch_op.drop_column('created_at') 