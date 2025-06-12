"""split narration texts into intro and supporting

Revision ID: split_narration_texts
Revises: add_created_at_to_tags
Create Date: 2024-03-21 10:00:00.000000

"""
from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect


# revision identifiers, used by Alembic.
revision: str = 'split_narration_texts'
down_revision: Union[str, None] = 'add_created_at_to_tags'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Get connection and inspector
    connection = op.get_bind()
    inspector = inspect(connection)
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('history')]
    
    # Add new columns if they don't exist
    with op.batch_alter_table('history') as batch_op:
        if 'intro_narration_texts' not in existing_columns:
            batch_op.add_column(sa.Column('intro_narration_texts', sa.Text(), nullable=True))
        if 'supporting_narration_texts' not in existing_columns:
            batch_op.add_column(sa.Column('supporting_narration_texts', sa.Text(), nullable=True))
    
    # Get all rows with narration_texts
    result = connection.execute(
        text("SELECT id, narration_texts FROM history WHERE narration_texts IS NOT NULL")
    )
    rows = result.fetchall()
    
    # Process each row
    for row in rows:
        try:
            # Parse existing narration texts
            narration_texts = json.loads(row[1]) if row[1] else []
            
            # Split into intro and supporting (assuming first text is intro)
            intro_texts = [narration_texts[0]] if narration_texts else []
            supporting_texts = narration_texts[1:] if len(narration_texts) > 1 else []
            
            # Update the row with new columns
            connection.execute(
                text("UPDATE history SET intro_narration_texts = :intro, supporting_narration_texts = :support WHERE id = :id"),
                {
                    "intro": json.dumps(intro_texts),
                    "support": json.dumps(supporting_texts),
                    "id": row[0]
                }
            )
        except Exception as e:
            print(f"Error processing row {row[0]}: {str(e)}")
            # If there's an error, set empty arrays
            connection.execute(
                text("UPDATE history SET intro_narration_texts = '[]', supporting_narration_texts = '[]' WHERE id = :id"),
                {"id": row[0]}
            )
    
    # Drop the old column if it exists
    if 'narration_texts' in existing_columns:
        with op.batch_alter_table('history') as batch_op:
            batch_op.drop_column('narration_texts')


def downgrade() -> None:
    """Downgrade schema."""
    # Get connection and inspector
    connection = op.get_bind()
    inspector = inspect(connection)
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('history')]
    
    # Add back the old column if it doesn't exist
    if 'narration_texts' not in existing_columns:
        with op.batch_alter_table('history') as batch_op:
            batch_op.add_column(sa.Column('narration_texts', sa.Text(), nullable=True))

    # Get all rows with both new columns
    result = connection.execute(
        text("SELECT id, intro_narration_texts, supporting_narration_texts FROM history")
    )
    rows = result.fetchall()
    
    # Process each row
    for row in rows:
        try:
            # Parse both text arrays
            intro_texts = json.loads(row[1]) if row[1] else []
            supporting_texts = json.loads(row[2]) if row[2] else []
            
            # Combine into single array
            combined_texts = intro_texts + supporting_texts
            
            # Update the row with combined texts
            connection.execute(
                text("UPDATE history SET narration_texts = :texts WHERE id = :id"),
                {
                    "texts": json.dumps(combined_texts),
                    "id": row[0]
                }
            )
        except Exception as e:
            print(f"Error processing row {row[0]}: {str(e)}")
            # If there's an error, set empty array
            connection.execute(
                text("UPDATE history SET narration_texts = '[]' WHERE id = :id"),
                {"id": row[0]}
            )
    
    # Drop the new columns if they exist
    with op.batch_alter_table('history') as batch_op:
        if 'intro_narration_texts' in existing_columns:
            batch_op.drop_column('intro_narration_texts')
        if 'supporting_narration_texts' in existing_columns:
            batch_op.drop_column('supporting_narration_texts') 