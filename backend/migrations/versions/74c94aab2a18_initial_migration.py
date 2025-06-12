"""Initial migration

Revision ID: 74c94aab2a18
Revises: 
Create Date: 2025-06-12 19:05:28.360929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = '74c94aab2a18'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)

    # Create prompts table
    op.create_table(
        'prompts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('embedding', sqlite.JSON, nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('key_concepts', sa.Text(), nullable=True),
        sa.Column('education_level', sa.String(50), nullable=True),
        sa.Column('learning_objectives', sa.Text(), nullable=True),
        sa.Column('interactive_features', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompts_topic'), 'prompts', ['topic'], unique=False)
    op.create_index(op.f('ix_prompts_subject'), 'prompts', ['subject'], unique=False)

    # Create prompt_tags association table
    op.create_table(
        'prompt_tags',
        sa.Column('prompt_id', sa.Integer(), nullable=True),
        sa.Column('tag_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], )
    )

    # Create history table
    op.create_table(
        'history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt_id', sa.Integer(), nullable=True),
        sa.Column('user_query', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('components', sqlite.JSON, nullable=True),
        sa.Column('materials', sqlite.JSON, nullable=True),
        sa.Column('lights', sqlite.JSON, nullable=True),
        sa.Column('render_settings', sqlite.JSON, nullable=True),
        sa.Column('animation_speed', sa.Float(), nullable=True),
        sa.Column('intro_narration_texts', sqlite.JSON, nullable=True),
        sa.Column('supporting_narration_texts', sqlite.JSON, nullable=True),
        sa.Column('scene_description', sa.String(), nullable=True),
        sa.Column('generation_time', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create visualizations table
    op.create_table(
        'visualizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('config', sqlite.JSON, nullable=True),
        sa.Column('embedding', sqlite.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_visualizations_topic'), 'visualizations', ['topic'], unique=False)
    op.create_index(op.f('ix_visualizations_subject'), 'visualizations', ['subject'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_index(op.f('ix_visualizations_subject'), table_name='visualizations')
    op.drop_index(op.f('ix_visualizations_topic'), table_name='visualizations')
    op.drop_table('visualizations')
    
    op.drop_table('history')
    
    op.drop_table('prompt_tags')
    
    op.drop_index(op.f('ix_prompts_subject'), table_name='prompts')
    op.drop_index(op.f('ix_prompts_topic'), table_name='prompts')
    op.drop_table('prompts')
    
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_table('tags')
