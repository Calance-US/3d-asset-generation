"""add user_query and response to history

Revision ID: add_user_query_and_response
Revises: add_prompt_id_to_history
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_user_query_and_response'
down_revision = 'add_prompt_id_to_history'
branch_labels = None
depends_on = None

def upgrade():
    # Add user_query and response columns to history table
    op.add_column('history', sa.Column('user_query', sa.Text(), nullable=True))
    op.add_column('history', sa.Column('response', sa.Text(), nullable=True))

    # Create a table object for the history table
    history = sa.table('history',
        sa.column('id', sa.Integer),
        sa.column('prompt', sa.Text),
        sa.column('html', sa.Text),
        sa.column('user_query', sa.Text),
        sa.column('response', sa.Text)
    )

    # Copy data from prompt to user_query and html to response
    op.execute(
        history.update().values(
            user_query=history.c.prompt,
            response=history.c.html
        )
    )


def downgrade():
    # Remove user_query and response columns
    op.drop_column('history', 'user_query')
    op.drop_column('history', 'response') 