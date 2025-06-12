"""add visualizations table

Revision ID: add_visualizations_table
Revises: remove_subject_from_history
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_visualizations_table'
down_revision = 'remove_subject_from_history'
branch_labels = None
depends_on = None

def upgrade():
    # Create visualizations table
    op.create_table(
        'visualizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('config', sqlite.JSON, nullable=True),
        sa.Column('embedding', sqlite.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create visualization_tags association table
    op.create_table(
        'visualization_tags',
        sa.Column('visualization_id', sa.Integer(), nullable=True),
        sa.Column('tag_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['visualization_id'], ['visualizations.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], )
    )

def downgrade():
    op.drop_table('visualization_tags')
    op.drop_table('visualizations') 