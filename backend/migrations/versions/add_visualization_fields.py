"""add visualization fields to history

Revision ID: add_visualization_fields
Revises: add_educational_fields
Create Date: 2025-06-10 14:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_visualization_fields'
down_revision: Union[str, None] = 'add_educational_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('history') as batch_op:
        batch_op.add_column(sa.Column('provider', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('components', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('materials', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('lights', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('render_settings', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('animation_speed', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('narration_texts', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('history') as batch_op:
        batch_op.drop_column('narration_texts')
        batch_op.drop_column('animation_speed')
        batch_op.drop_column('render_settings')
        batch_op.drop_column('lights')
        batch_op.drop_column('materials')
        batch_op.drop_column('components')
        batch_op.drop_column('provider') 