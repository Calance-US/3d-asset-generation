"""add created_at to history

Revision ID: add_created_at_to_history
Revises: add_user_query_and_response
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision = 'add_created_at_to_history'
down_revision = 'add_user_query_and_response'
branch_labels = None
depends_on = None

def upgrade():
    # Add created_at column to history table with default value
    op.add_column('history', sa.Column('created_at', sa.DateTime(), nullable=True))

    history = table('history', column('created_at', DateTime()))
    op.execute(
        history.update().where(history.c.created_at == None).values(created_at=func.current_timestamp())
    )

def downgrade():
    # Remove created_at column
    op.drop_column('history', 'created_at') 