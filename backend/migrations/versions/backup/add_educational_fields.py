"""add educational fields to prompt

Revision ID: add_educational_fields
Revises: add_foreign_key_to_history
Create Date: 2025-06-10 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_educational_fields'
down_revision: Union[str, None] = 'add_foreign_key_to_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('prompts') as batch_op:
        batch_op.add_column(sa.Column('key_concepts', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('education_level', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('learning_objectives', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('interactive_features', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('prompts') as batch_op:
        batch_op.drop_column('interactive_features')
        batch_op.drop_column('learning_objectives')
        batch_op.drop_column('education_level')
        batch_op.drop_column('key_concepts') 