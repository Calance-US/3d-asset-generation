"""remove subject from history

Revision ID: remove_subject_from_history
Revises: add_generation_time_to_history
Create Date: 2024-03-19 15:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'remove_subject_from_history'
down_revision: Union[str, None] = 'add_generation_time_to_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the subject column from history table
    op.drop_column('history', 'subject')


def downgrade() -> None:
    # Add back the subject column to history table
    op.add_column('history', sa.Column('subject', sa.String(), nullable=True)) 