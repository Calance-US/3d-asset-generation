"""add embedding column

Revision ID: add_embedding_column
Revises: ee13f9c23462
Create Date: 2024-03-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON


# revision identifiers, used by Alembic.
revision: str = 'add_embedding_column'
down_revision: Union[str, None] = 'ee13f9c23462'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create a new table with the updated schema
    op.create_table(
        'prompts_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('embedding', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompts_new_category'), 'prompts_new', ['category'], unique=False)
    op.create_index(op.f('ix_prompts_new_subject'), 'prompts_new', ['subject'], unique=False)
    op.create_index(op.f('ix_prompts_new_topic'), 'prompts_new', ['topic'], unique=False)

    # Copy data from the old table to the new table
    op.execute('INSERT INTO prompts_new (id, topic, subject, content, category) SELECT id, topic, subject, content, category FROM prompts')

    # Drop the old table
    op.drop_table('prompts')

    # Rename the new table to the old table's name
    op.rename_table('prompts_new', 'prompts')


def downgrade() -> None:
    """Downgrade schema."""
    # Create a new table with the original schema
    op.create_table(
        'prompts_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompts_old_category'), 'prompts_old', ['category'], unique=False)
    op.create_index(op.f('ix_prompts_old_subject'), 'prompts_old', ['subject'], unique=False)
    op.create_index(op.f('ix_prompts_old_topic'), 'prompts_old', ['topic'], unique=False)

    # Copy data back to the old table
    op.execute('INSERT INTO prompts_old (id, topic, subject, content, category) SELECT id, topic, subject, content, category FROM prompts')

    # Drop the new table
    op.drop_table('prompts')

    # Rename the old table back
    op.rename_table('prompts_old', 'prompts') 