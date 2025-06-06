from sqlalchemy import create_engine, Column, String, Table, ForeignKey, Integer, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create SQLite database engine
DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def run_migration():
    """Run the migration to add category and tags."""
    with engine.connect() as conn:
        # Drop the existing 'prompts_new' table if it exists
        conn.execute(text("DROP TABLE IF EXISTS prompts_new"))
        # Create a new table without the 'category' column
        conn.execute(text("CREATE TABLE prompts_new (id INTEGER PRIMARY KEY, topic VARCHAR, subject VARCHAR, content VARCHAR)"))
        # Copy data from the old table to the new table
        conn.execute(text("INSERT INTO prompts_new (id, topic, subject, content) SELECT id, topic, subject, content FROM prompts"))
        # Drop the old table
        conn.execute(text("DROP TABLE prompts"))
        # Rename the new table to the old table's name
        conn.execute(text("ALTER TABLE prompts_new RENAME TO prompts"))
        # Add the 'category' column
        conn.execute(text("ALTER TABLE prompts ADD COLUMN category VARCHAR"))
        # Create the 'tags' table if it doesn't exist
        conn.execute(text("CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY, name VARCHAR UNIQUE)"))
        # Create the 'prompt_tags' association table if it doesn't exist
        conn.execute(text("CREATE TABLE IF NOT EXISTS prompt_tags (prompt_id INTEGER, tag_id INTEGER, FOREIGN KEY (prompt_id) REFERENCES prompts(id), FOREIGN KEY (tag_id) REFERENCES tags(id))"))
        conn.commit()

if __name__ == "__main__":
    run_migration() 