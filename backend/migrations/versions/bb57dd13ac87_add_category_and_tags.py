"""add category and tags

Revision ID: bb57dd13ac87
Revises:
Create Date: 2023-10-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb57dd13ac87'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create a new table with the updated schema
    conn = op.get_bind()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tags';").fetchall()
    if not tables:
        op.create_table(
            'prompts_new',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('topic', sa.String(), nullable=True),
            sa.Column('subject', sa.String(), nullable=True),
            sa.Column('content', sa.String(), nullable=True),
            sa.Column('category', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_prompts_new_category'), 'prompts_new', ['category'], unique=False)
        op.create_index(op.f('ix_prompts_new_subject'), 'prompts_new', ['subject'], unique=False)
        op.create_index(op.f('ix_prompts_new_topic'), 'prompts_new', ['topic'], unique=False)

    # Copy data from the old table to the new table
    op.execute('INSERT INTO prompts_new (id, topic, subject, content) SELECT id, topic, subject, content FROM prompts')

    # Drop the old table
    op.drop_table('prompts')

    # Rename the new table to the old table's name
    op.rename_table('prompts_new', 'prompts')

    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)

    # Create prompt_tags association table
    op.create_table(
        'prompt_tags',
        sa.Column('prompt_id', sa.Integer(), nullable=True),
        sa.Column('tag_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], )
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the prompt_tags association table
    op.drop_table('prompt_tags')

    # Drop the tags table
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_table('tags')

    # Revert prompts table to its original state
    op.create_table(
        'prompts_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('content', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompts_old_subject'), 'prompts_old', ['subject'], unique=False)
    op.create_index(op.f('ix_prompts_old_topic'), 'prompts_old', ['topic'], unique=False)

    # Copy data back to the old table
    op.execute('INSERT INTO prompts_old (id, topic, subject, content) SELECT id, topic, subject, content FROM prompts')

    # Drop the new table
    op.drop_table('prompts')

    # Rename the old table back
    op.rename_table('prompts_old', 'prompts')
