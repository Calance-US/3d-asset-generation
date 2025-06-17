"""Create snippet metadata table.

Revision ID: 2024_03_19_0001
Revises: 2025_06_16_1050  # This is the first migration
Create Date: 2024-03-19 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2024_03_19_0001'
down_revision = '2025_06_16_1050'  # This is the first migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create snippet_metadata table
    op.create_table(
        'snippet_metadata',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('snippet_hash', sa.String(), nullable=False),
        sa.Column('snippet_type', sa.String(), nullable=True),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('embedding_text', sa.String(), nullable=True),
        sa.Column('html_snippet', sa.String(), nullable=True),
        sa.Column('filename', sa.String(), nullable=True),
        sa.Column('upload_id', sa.String(36), nullable=True),
        sa.Column('llm_version', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('validation_status', sa.String(), nullable=True),
        sa.Column('validation_errors', sa.JSON(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('key_concepts', sa.String(), nullable=True),
        sa.Column('education_level', sa.String(), nullable=True),
        sa.Column('learning_objectives', sa.String(), nullable=True)
    )
    
    # Create indexes
    op.create_index('ix_snippet_metadata_snippet_hash', 'snippet_metadata', ['snippet_hash'], unique=True)
    op.create_index('ix_snippet_metadata_upload_id', 'snippet_metadata', ['upload_id'])
    op.create_index('ix_snippet_metadata_created_at', 'snippet_metadata', ['created_at'])
    op.create_index('ix_snippet_metadata_updated_at', 'snippet_metadata', ['updated_at'])

def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_snippet_metadata_updated_at', table_name='snippet_metadata')
    op.drop_index('ix_snippet_metadata_created_at', table_name='snippet_metadata')
    op.drop_index('ix_snippet_metadata_upload_id', table_name='snippet_metadata')
    op.drop_index('ix_snippet_metadata_snippet_hash', table_name='snippet_metadata')
    
    # Drop table
    op.drop_table('snippet_metadata') 