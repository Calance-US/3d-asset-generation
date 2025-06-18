"""Add faiss_id column to snippet_metadata for FAISS/metadata linkage.

Revision ID: 2025_06_17_0001
Revises: 2024_03_19_0001
Create Date: 2025-06-17 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2025_06_17_0001'
down_revision = '2024_03_19_0001'
branch_labels = None
depends_on = None

def upgrade():
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('snippet_metadata') as batch_op:
        batch_op.add_column(sa.Column('faiss_id', sa.BigInteger(), nullable=True))
    # Now add a unique index (works for both SQLite and Postgres)
    op.create_index('ix_snippet_metadata_faiss_id', 'snippet_metadata', ['faiss_id'], unique=True)

def downgrade():
    op.drop_index('ix_snippet_metadata_faiss_id', table_name='snippet_metadata')
    with op.batch_alter_table('snippet_metadata') as batch_op:
        batch_op.drop_column('faiss_id') 