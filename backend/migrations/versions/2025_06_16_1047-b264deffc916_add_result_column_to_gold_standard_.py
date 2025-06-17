"""add_result_column_to_gold_standard_upload_status

Revision ID: b264deffc916
Revises: e7c7d9ac9c85
Create Date: 2025-06-16 10:47:22.338136+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b264deffc916'
down_revision: Union[str, None] = 'e7c7d9ac9c85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add result column as Text (SQLite doesn't have native JSON type)
    op.add_column('gold_standard_upload_status',
        sa.Column('result', sa.Text, nullable=True)
    )
    # Add error_message column
    op.add_column('gold_standard_upload_status',
        sa.Column('error_message', sa.Text, nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the columns
    op.drop_column('gold_standard_upload_status', 'result')
    op.drop_column('gold_standard_upload_status', 'error_message')
