"""Service for managing snippet metadata in the RAG system."""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.database.db_config import get_db
from app.models import SnippetMetadata

logger = logging.getLogger(__name__)


class MetadataService:
    """Service for managing snippet metadata operations in the RAG system."""

    def __init__(self, db: Session):
        self.db = db

    async def add_snippet(
        self, snippet_data: Dict[str, Any], faiss_id: int = None
    ) -> SnippetMetadata:
        """Add a new snippet to the metadata store, optionally setting faiss_id."""
        try:
            if faiss_id is not None:
                snippet_data["faiss_id"] = faiss_id
            snippet = SnippetMetadata(**snippet_data)
            self.db.add(snippet)
            self.db.commit()
            self.db.refresh(snippet)
            return snippet
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding snippet to metadata store: {str(e)}")
            raise

    async def get_by_hash(self, snippet_hash: str) -> Optional[SnippetMetadata]:
        """Get a snippet by its hash."""
        return (
            self.db.query(SnippetMetadata).filter_by(snippet_hash=snippet_hash).first()
        )

    async def update_snippet(
        self, snippet_hash: str, update_data: Dict[str, Any]
    ) -> Optional[SnippetMetadata]:
        """Update an existing snippet."""
        try:
            snippet = (
                self.db.query(SnippetMetadata)
                .filter_by(snippet_hash=snippet_hash)
                .first()
            )
            if snippet:
                for key, value in update_data.items():
                    setattr(snippet, key, value)
                self.db.commit()
                self.db.refresh(snippet)
            return snippet
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating snippet in metadata store: {str(e)}")
            raise

    async def get_by_upload_id(self, upload_id: uuid.UUID) -> List[SnippetMetadata]:
        """Get all snippets for a specific upload."""
        return self.db.query(SnippetMetadata).filter_by(upload_id=upload_id).all()


def get_metadata_service() -> MetadataService:
    """Get a metadata service instance with a database session."""
    db = next(get_db())
    return MetadataService(db)
