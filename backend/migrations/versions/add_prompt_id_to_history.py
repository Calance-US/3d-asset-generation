"""add prompt_id to history

Revision ID: add_prompt_id_to_history
Revises: add_embedding_column
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_prompt_id_to_history'
down_revision = 'add_embedding_column'
branch_labels = None
depends_on = None

def upgrade():
    # Add prompt_id column to history table
    op.add_column('history', sa.Column('prompt_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_history_prompt_id',
        'history', 'prompts',
        ['prompt_id'], ['id']
    )

def downgrade():
    # Remove foreign key and prompt_id column
    op.drop_constraint('fk_history_prompt_id', 'history', type_='foreignkey')
    op.drop_column('history', 'prompt_id') 