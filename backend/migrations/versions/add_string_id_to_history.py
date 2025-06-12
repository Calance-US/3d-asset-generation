"""Add string id to history table

Revision ID: add_string_id_to_history
Revises: add_visualization_tags
Create Date: 2024-03-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_string_id_to_history'
down_revision: Union[str, None] = 'add_visualization_tags'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create a new history table with string id
    op.create_table(
        'history_new',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('prompt_id', sa.Integer(), nullable=True),
        sa.Column('user_query', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('components', sa.JSON(), nullable=True),
        sa.Column('materials', sa.JSON(), nullable=True),
        sa.Column('lights', sa.JSON(), nullable=True),
        sa.Column('render_settings', sa.JSON(), nullable=True),
        sa.Column('animation_speed', sa.Float(), nullable=True),
        sa.Column('intro_narration_texts', sa.JSON(), nullable=True),
        sa.Column('supporting_narration_texts', sa.JSON(), nullable=True),
        sa.Column('scene_description', sa.String(), nullable=True),
        sa.Column('generation_time', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Copy data from old table to new table
    op.execute('INSERT INTO history_new SELECT * FROM history')

    # Drop old table
    op.drop_table('history')

    # Rename new table to old table name
    op.rename_table('history_new', 'history')


def downgrade() -> None:
    """Downgrade schema."""
    # Create a new history table with integer id
    op.create_table(
        'history_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt_id', sa.Integer(), nullable=True),
        sa.Column('user_query', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('components', sa.JSON(), nullable=True),
        sa.Column('materials', sa.JSON(), nullable=True),
        sa.Column('lights', sa.JSON(), nullable=True),
        sa.Column('render_settings', sa.JSON(), nullable=True),
        sa.Column('animation_speed', sa.Float(), nullable=True),
        sa.Column('intro_narration_texts', sa.JSON(), nullable=True),
        sa.Column('supporting_narration_texts', sa.JSON(), nullable=True),
        sa.Column('scene_description', sa.String(), nullable=True),
        sa.Column('generation_time', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Copy data from old table to new table (only rows with numeric IDs)
    op.execute('INSERT INTO history_new SELECT * FROM history WHERE CAST(id AS INTEGER) = id')

    # Drop old table
    op.drop_table('history')

    # Rename new table to old table name
    op.rename_table('history_new', 'history') 