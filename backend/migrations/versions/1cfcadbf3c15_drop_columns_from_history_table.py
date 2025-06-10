"""drop columns from history table

Revision ID: 1cfcadbf3c15
Revises: add_created_at_to_history
Create Date: 2025-06-10 13:50:39.977112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cfcadbf3c15'
down_revision: Union[str, None] = 'add_created_at_to_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the old columns
    op.drop_column('history', 'prompt')
    op.drop_column('history', 'html')
    op.drop_column('history', 'timestamp')


def downgrade() -> None:
    """Downgrade schema."""
    # Add back the old columns
    op.add_column('history', sa.Column('prompt', sa.Text(), nullable=True))
    op.add_column('history', sa.Column('html', sa.Text(), nullable=True))
    op.add_column('history', sa.Column('timestamp', sa.DateTime(), nullable=True))
