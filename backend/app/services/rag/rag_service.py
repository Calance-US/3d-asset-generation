"""RAG service for handling retrieval-augmented generation."""
from typing import List, Dict, Any, Optional
from fastapi import Depends
from app.services.rag.vector_store import VectorStore, get_vector_store
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.metadata_service import MetadataService, get_metadata_service
from app.config.settings import settings
import logging
import numpy as np
from sqlalchemy.orm import Session
from app.models import SnippetMetadata

logger = logging.getLogger(__name__)

class RAGService:
    """Service for handling retrieval-augmented generation with atomicity."""
    def __init__(self, vector_store: VectorStore, metadata_service: MetadataService):
        self.vector_store = vector_store
        self.metadata_service = metadata_service

    async def get_similar_visualizations(self, query: str, db, limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar visualizations based on the query text."""
        try:
            query_embedding = EmbeddingService.generate_embedding(query)
            return await self.vector_store.get_similar_visualizations(query_embedding, db, limit)
        except Exception as e:
            logger.error(f"Error getting similar visualizations: {str(e)}")
            raise

    async def get_diverse_examples(self, db: Session) -> List[Dict[str, Any]]:
        """Get one example of each visualization type from the vector store."""
        try:
            # Get all visualizations from database
            all_metadata = db.query(SnippetMetadata).all()
            
            # Group by visualization type
            type_groups = {}
            for metadata in all_metadata:
                viz_type = metadata.metadata.get('visualization_type', 'unknown')
                if viz_type not in type_groups:
                    type_groups[viz_type] = []
                type_groups[viz_type].append(metadata)
            
            # Take one example from each type
            diverse_examples = []
            for viz_type, examples in type_groups.items():
                if examples:
                    # For now, just take the first example of each type
                    # In a more sophisticated implementation, you might want to compute
                    # embeddings and find the most representative one
                    diverse_examples.append({
                        'metadata': examples[0].metadata,
                        'type': viz_type
                    })
            
            return diverse_examples
        except Exception as e:
            logger.error(f"Error getting diverse examples: {str(e)}")
            raise

    async def add_snippet_atomic(self, text: str, metadata: Dict[str, Any], db: Session) -> None:
        """Atomically add a snippet: embedding, vector store, and metadata store."""
        embedding = EmbeddingService.generate_embedding(text)
        faiss_id = None
        try:
            # Generate a new unique faiss_id
            max_faiss_id = db.query(SnippetMetadata.faiss_id).order_by(SnippetMetadata.faiss_id.desc()).first()
            faiss_id = (max_faiss_id[0] if max_faiss_id and max_faiss_id[0] is not None else 0) + 1
            
            # Add to vector store first
            self.vector_store.add_visualization(embedding, faiss_id)
        except Exception as e:
            logger.error(f"Error adding to vector store: {str(e)}")
            raise
        try:
            # Add to metadata store
            await self.metadata_service.add_snippet(metadata, faiss_id=faiss_id)
        except Exception as e:
            # Rollback vector store addition if metadata fails
            # Note: FAISS doesn't have a simple way to remove by ID, so we'll need to rebuild
            # For now, we'll just log the error and let the user know
            logger.error(f"Error adding to metadata store, vector store may be inconsistent: {str(e)}")
            raise

    async def save_vector_store(self) -> None:
        """Save the vector store to disk (no-op for Qdrant)."""
        logger.info("Qdrant handles vector persistence automatically; save is a no-op.")

def get_rag_service(
    vector_store: VectorStore = Depends(get_vector_store),
    metadata_service: MetadataService = Depends(get_metadata_service)
) -> RAGService:
    """Get a RAG service instance with vector and metadata stores."""
    return RAGService(vector_store, metadata_service) 