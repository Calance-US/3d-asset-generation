import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.database.db_config import SessionLocal
from app.models import HistoryEntry, Prompt, Tag, prompt_tags

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


# Initialize prompt selector
prompt_selector = None


def get_prompt_selector():
    """Get or create the PromptSelector instance."""
    global prompt_selector
    if prompt_selector is None:
        from ..services.prompt_selector import PromptSelector

        prompt_selector = PromptSelector()
    return prompt_selector


# Database dependency
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# History operations
def get_all_history(db):
    return db.query(HistoryEntry).order_by(HistoryEntry.created_at.desc()).all()


def get_history_entry_by_id(db, entry_id: str):
    return db.query(HistoryEntry).filter(HistoryEntry.id == entry_id).first()


def create_history_entry(db, entry: dict):
    db_entry = HistoryEntry(**entry)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


def remove_history_entry(db, entry_id: str):
    db.query(HistoryEntry).filter(HistoryEntry.id == entry_id).delete()
    db.commit()


# Prompt operations
def get_prompts(
    db,
    subject: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
):
    query = db.query(Prompt)

    if subject:
        query = query.filter(Prompt.subject == subject)
    if category:
        query = query.filter(Prompt.category == category)
    if tag:
        query = query.join(prompt_tags).join(Tag).filter(Tag.name == tag)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Prompt.topic.ilike(search_term))
            | (Prompt.content.ilike(search_term))
            | (Prompt.subject.ilike(search_term))
        )

    return query.all()


def create_prompt(
    db: Session,
    subject: str,
    topic: str,
    content: str,
    category: Optional[str] = None,
    key_concepts: Optional[str] = None,
    education_level: Optional[str] = None,
    learning_objectives: Optional[str] = None,
    interactive_features: Optional[str] = None,
    tags: Optional[str] = None,
) -> Prompt:
    """Create a new prompt in the database."""
    # Log the values being saved
    logger.info(
        "Saving prompt with values:",
        extra={
            "action": "create_prompt",
            "values": {
                "subject": subject,
                "topic": topic,
                "content": content,
                "category": category,
                "key_concepts": key_concepts,
                "education_level": education_level,
                "learning_objectives": learning_objectives,
                "interactive_features": interactive_features,
            },
        },
    )

    prompt = Prompt(
        subject=subject,
        topic=topic,
        content=content,
        category=category,
        key_concepts=key_concepts,
        education_level=education_level,
        learning_objectives=learning_objectives,
        interactive_features=interactive_features,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Add tags if provided
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag_name in tag_list:
            # Get or create tag
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
            prompt.tags.append(tag)

    db.add(prompt)
    db.commit()
    db.refresh(prompt)

    # Log the saved values
    logger.info(
        "Saved prompt with values:",
        extra={
            "action": "create_prompt",
            "saved_values": {
                "id": prompt.id,
                "subject": prompt.subject,
                "topic": prompt.topic,
                "content": prompt.content,
                "category": prompt.category,
                "key_concepts": prompt.key_concepts,
                "education_level": prompt.education_level,
                "learning_objectives": prompt.learning_objectives,
                "interactive_features": prompt.interactive_features,
            },
        },
    )

    return prompt


def update_prompt(db: Session, prompt_id: int, update_data: dict) -> Optional[Prompt]:
    """
    Update a prompt in the database.

    Args:
        db: Database session
        prompt_id: ID of the prompt to update
        update_data: Dictionary containing fields to update

    Returns:
        Updated Prompt object or None if not found
    """
    try:
        # Get the prompt
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            return None

        # Update basic fields
        if "subject" in update_data:
            prompt.subject = update_data["subject"]
        if "topic" in update_data:
            prompt.topic = update_data["topic"]
        if "content" in update_data:
            prompt.content = update_data["content"]
        if "category" in update_data:
            prompt.category = update_data["category"]

        # Handle tags
        if "tags" in update_data:
            # Clear existing tags
            prompt.tags = []

            # Add new tags
            if update_data["tags"]:
                # Split tags by comma and strip whitespace
                tag_names = [
                    tag.strip() for tag in update_data["tags"].split(",") if tag.strip()
                ]

                # Get or create tags
                for tag_name in tag_names:
                    tag = db.query(Tag).filter(Tag.name == tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.add(tag)
                    prompt.tags.append(tag)

        db.commit()
        db.refresh(prompt)
        return prompt

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating prompt: {str(e)}")
        raise


def delete_prompt(db: Session, prompt_id: int) -> bool:
    """
    Delete a prompt from the database.

    Args:
        db: Database session
        prompt_id: ID of the prompt to delete

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            return False

        db.delete(prompt)
        db.commit()

        # Update FAISS index
        get_prompt_selector().initialize_index()

        return True
    except Exception as e:
        db.rollback()
        logging.error(f"Error deleting prompt: {str(e)}")
        return False


def duplicate_prompt(db, prompt_id: int) -> Optional[Prompt]:
    """Duplicate a prompt with all its tags."""
    try:
        original = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not original:
            return None

        # Create new prompt with copied data
        new_prompt = Prompt(
            subject=original.subject,
            topic=f"{original.topic} (Copy)",
            content=original.content,
            category=original.category,
        )

        # Copy tags
        new_prompt.tags = original.tags.copy()

        db.add(new_prompt)
        db.commit()
        db.refresh(new_prompt)
        return new_prompt
    except Exception as e:
        db.rollback()
        logging.error(f"Error duplicating prompt: {str(e)}")
        return None


def batch_delete_prompts(db, prompt_ids: List[int]) -> bool:
    """Delete multiple prompts by their IDs."""
    try:
        db.query(Prompt).filter(Prompt.id.in_(prompt_ids)).delete(
            synchronize_session=False
        )
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logging.error(f"Error deleting prompts: {str(e)}")
        return False


def export_prompts(db) -> List[Dict]:
    """Export all prompts with their tags."""
    prompts = db.query(Prompt).all()
    return [
        {
            "id": p.id,
            "subject": p.subject,
            "topic": p.topic,
            "content": p.content,
            "category": p.category,
            "tags": [tag.name for tag in p.tags],
        }
        for p in prompts
    ]


def import_prompts(db, prompts_data: List[Dict]) -> bool:
    """Import prompts from a list of dictionaries.

    Args:
        db: Database session
        prompts_data: List of dictionaries containing prompt data
            Each dictionary should have:
            - subject (str): The subject area
            - topic (str): The prompt topic
            - content (str): The prompt content
            - category (str, optional): The prompt category
            - tags (List[str], optional): List of tags

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        for prompt_data in prompts_data:
            # Validate required fields
            if not all(key in prompt_data for key in ["subject", "topic", "content"]):
                raise ValueError(
                    "Each prompt must have subject, topic, and content fields"
                )

            # Create the prompt with optional fields
            create_prompt(
                db,
                subject=prompt_data["subject"],
                topic=prompt_data["topic"],
                content=prompt_data["content"],
                category=prompt_data.get("category"),
                key_concepts=prompt_data.get("key_concepts"),
                education_level=prompt_data.get("education_level"),
                learning_objectives=prompt_data.get("learning_objectives"),
                interactive_features=prompt_data.get("interactive_features"),
                tags=prompt_data.get("tags", ""),
            )
        db.commit()

        # Update FAISS index
        get_prompt_selector().initialize_index()

        return True
    except Exception as e:
        db.rollback()
        logging.error(f"Error importing prompts: {str(e)}")
        return False


# Migration function to move data from JSON files to SQLite
def migrate_from_json():
    db = SessionLocal()
    try:
        # Clear existing data before migration
        db.query(HistoryEntry).delete()
        db.query(Prompt).delete()
        db.commit()

        # Migrate history
        history_file = Path(__file__).parent / "data" / "history.json"
        if history_file.exists():
            with open(history_file, "r") as f:
                history_data = json.load(f)
                for entry in history_data:
                    # Map the fields correctly, handling both 'topic' and 'prompt' fields
                    db_entry = {
                        "id": entry["id"],
                        "prompt": entry.get(
                            "prompt", entry.get("topic", "")
                        ),  # Try 'prompt' first, fall back to 'topic'
                        "provider": entry["provider"],
                        "subject": entry.get("subject", ""),  # Make subject optional
                        "html": entry["html"],
                        "timestamp": datetime.fromisoformat(entry["timestamp"]),
                    }
                    create_history_entry(db, db_entry)

        # Migrate prompts
        prompts_dir = Path(__file__).parent / "prompts"
        if prompts_dir.exists():
            # Handle .txt prompt files
            for prompt_file in prompts_dir.glob("*.prompt.txt"):
                subject = "physics"  # Default subject
                if "chemistry" in prompt_file.name:
                    subject = "chemistry"
                elif "biology" in prompt_file.name:
                    subject = "biology"

                with open(prompt_file, "r") as f:
                    prompt_content = f.read()
                    create_prompt(db, subject, prompt_file.stem, prompt_content)

    finally:
        db.close()


def get_prompt_by_id(self, prompt_id: int) -> Optional[Prompt]:
    """Get a prompt by its ID."""
    try:
        return self.session.query(Prompt).filter(Prompt.id == prompt_id).first()
    except Exception as e:
        logger.error(
            "Error getting prompt by ID",
            extra={
                "action": "get_prompt_by_id",
                "prompt_id": prompt_id,
                "error": str(e),
            },
        )
        return None


def get_prompt_by_name(self, name: str) -> Optional[Prompt]:
    """Get a prompt by its name."""
    try:
        return self.session.query(Prompt).filter(Prompt.name == name).first()
    except Exception as e:
        logger.error(
            "Error getting prompt by name",
            extra={"action": "get_prompt_by_name", "name": name, "error": str(e)},
        )
        return None


def prompt_exists(self, name: str) -> bool:
    """Check if a prompt with the given name exists."""
    try:
        return bool(self.session.query(Prompt).filter(Prompt.name == name).first())
    except Exception as e:
        logger.error(
            "Error checking prompt existence",
            extra={"action": "prompt_exists", "name": name, "error": str(e)},
        )
        return False
