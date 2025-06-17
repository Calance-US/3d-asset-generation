"""recreate gold standard upload status table

Revision ID: 2025_06_16_1050
Revises: b264deffc916
Create Date: 2025-06-16 10:50:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2025_06_16_1050'
down_revision: Union[str, None] = 'b264deffc916'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the existing table
    op.drop_table('gold_standard_upload_status')
    
    # Create the table with the correct schema
    op.create_table(
        'gold_standard_upload_status',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('result', sa.Text, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the table
    op.drop_table('gold_standard_upload_status') 