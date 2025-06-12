"""add foreign key to history

Revision ID: add_foreign_key_to_history
Revises: 1cfcadbf3c15
Create Date: 2025-06-10 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_foreign_key_to_history'
down_revision: Union[str, None] = '1cfcadbf3c15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table('history') as batch_op:
        batch_op.create_foreign_key(
            'fk_history_prompt_id',
            'prompts',
            ['prompt_id'], ['id'],
            ondelete='CASCADE'  # If a prompt is deleted, delete associated history entries
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table('history') as batch_op:
        batch_op.drop_constraint('fk_history_prompt_id', type_='foreignkey') 