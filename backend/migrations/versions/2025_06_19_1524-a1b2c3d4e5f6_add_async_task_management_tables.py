"""add_async_task_management_tables

Revision ID: a1b2c3d4e5f6
Revises: 21ba1eb51833
Create Date: 2025-06-19 15:24:44.722533+00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "21ba1eb51833"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create async_tasks table
    op.create_table(
        "async_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("request_data", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress_percentage", sa.Integer(), nullable=True),
        sa.Column("current_stage", sa.String(length=50), nullable=True),
        sa.Column("total_stages", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for async_tasks table
    op.create_index(op.f("ix_async_tasks_id"), "async_tasks", ["id"], unique=False)
    op.create_index(
        op.f("ix_async_tasks_task_type"), "async_tasks", ["task_type"], unique=False
    )
    op.create_index(
        op.f("ix_async_tasks_status"), "async_tasks", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_async_tasks_created_at"), "async_tasks", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_async_tasks_updated_at"), "async_tasks", ["updated_at"], unique=False
    )

    # Create async_task_stages table
    op.create_table(
        "async_task_stages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("progress_percentage", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["async_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for async_task_stages table
    op.create_index(
        op.f("ix_async_task_stages_id"), "async_task_stages", ["id"], unique=False
    )

    # Set default values for new columns
    op.execute(
        "UPDATE async_tasks SET progress_percentage = 0 WHERE progress_percentage IS NULL"
    )
    op.execute("UPDATE async_tasks SET total_stages = 1 WHERE total_stages IS NULL")
    op.execute(
        "UPDATE async_task_stages SET progress_percentage = 0 WHERE progress_percentage IS NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes for async_task_stages table
    op.drop_index(op.f("ix_async_task_stages_id"), table_name="async_task_stages")

    # Drop async_task_stages table
    op.drop_table("async_task_stages")

    # Drop indexes for async_tasks table
    op.drop_index(op.f("ix_async_tasks_updated_at"), table_name="async_tasks")
    op.drop_index(op.f("ix_async_tasks_created_at"), table_name="async_tasks")
    op.drop_index(op.f("ix_async_tasks_status"), table_name="async_tasks")
    op.drop_index(op.f("ix_async_tasks_task_type"), table_name="async_tasks")
    op.drop_index(op.f("ix_async_tasks_id"), table_name="async_tasks")

    # Drop async_tasks table
    op.drop_table("async_tasks")
