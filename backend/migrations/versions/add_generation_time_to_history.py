"""add generation_time to history

Revision ID: add_generation_time_to_history
Revises: add_scene_description_to_history
Create Date: 2024-03-20 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_generation_time_to_history'
down_revision: Union[str, None] = 'add_scene_description_to_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('history') as batch_op:
        batch_op.add_column(sa.Column('generation_time', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('history') as batch_op:
        batch_op.drop_column('generation_time') 