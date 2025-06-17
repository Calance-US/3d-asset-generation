"""add gold standard upload status table

Revision ID: e7c7d9ac9c85
Revises: add_string_id_to_history
Create Date: 2025-06-16 10:23:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = 'e7c7d9ac9c85'
down_revision = 'add_string_id_to_history'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Conditionally alter column for non-SQLite
    conn = op.get_bind()
    if conn.dialect.name != "sqlite":
        op.alter_column('tags', 'name',
            existing_type=sa.String(length=255),
            nullable=True
        )
    # 2. Create new table as normal
    op.create_table(
        'gold_standard_upload_status',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

def downgrade():
    # 1. Drop the new table
    op.drop_table('gold_standard_upload_status')
    # 2. Conditionally revert the column change for non-SQLite
    conn = op.get_bind()
    if conn.dialect.name != "sqlite":
        op.alter_column('tags', 'name',
            existing_type=sa.String(length=255),
            nullable=False
        )
