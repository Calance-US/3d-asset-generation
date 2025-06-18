"""Set autoincrement=True on prompts.id column

Revision ID: 2025_06_18_0001
Revises: 2025_06_17_0001
Create Date: 2025-06-18 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2025_06_18_0001'
down_revision = '2025_06_17_0001'
branch_labels = None
depends_on = None

def upgrade():
    # For Postgres, alter column to set autoincrement (serial/identity)
    # For SQLite, this is a no-op if already INTEGER PRIMARY KEY
    # This migration is safe for both
    with op.batch_alter_table('prompts') as batch_op:
        batch_op.alter_column('id',
            existing_type=sa.Integer(),
            autoincrement=True,
            existing_nullable=False,
            existing_primary_key=True
        )

def downgrade():
    # Downgrade does not remove autoincrement, as it's not always reversible
    pass 