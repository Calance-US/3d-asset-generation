"""Add visualization tags table

Revision ID: add_visualization_tags
Revises: 74c94aab2a18
Create Date: 2024-03-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_visualization_tags'
down_revision: Union[str, None] = '74c94aab2a18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create visualization_tags association table
    op.create_table(
        'visualization_tags',
        sa.Column('visualization_id', sa.Integer(), nullable=True),
        sa.Column('tag_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['visualization_id'], ['visualizations.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('visualization_tags') 