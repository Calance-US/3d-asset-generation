"""RAG service for handling retrieval-augmented generation."""
from typing import List, Dict, Any, Optional
from fastapi import Depends
from app.services.rag.vector_store import VectorStore, get_vector_store
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.metadata_service import MetadataService, get_metadata_service
from app.config.settings import settings
import logging
import numpy as np

logger = logging.getLogger(__name__)

class RAGService:
    """Service for handling retrieval-augmented generation with atomicity."""
    def __init__(self, vector_store: VectorStore, metadata_service: MetadataService):
        self.vector_store = vector_store
        self.metadata_service = metadata_service

    async def get_similar_visualizations(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar visualizations based on the query text."""
        try:
            query_embedding = EmbeddingService.generate_embedding(query)
            return await self.vector_store.get_similar_visualizations(query_embedding, limit)
        except Exception as e:
            logger.error(f"Error getting similar visualizations: {str(e)}")
            raise

    async def get_diverse_examples(self) -> List[Dict[str, Any]]:
        """Get one example of each visualization type from the vector store."""
        try:
            # Get all visualizations
            all_viz = self.vector_store.visualizations
            
            # Group by visualization type
            type_groups = {}
            for viz in all_viz:
                viz_type = viz['metadata'].get('visualization_type', 'unknown')
                if viz_type not in type_groups:
                    type_groups[viz_type] = []
                type_groups[viz_type].append(viz)
            
            # Take one example from each type
            diverse_examples = []
            for viz_type, examples in type_groups.items():
                if examples:
                    # Sort by similarity to the first example to get a representative one
                    first_embedding = examples[0]['embedding']
                    similarities = [
                        self.vector_store._compute_similarity(first_embedding, ex['embedding'])
                        for ex in examples
                    ]
                    best_idx = np.argmax(similarities)
                    diverse_examples.append({
                        'metadata': examples[best_idx]['metadata'],
                        'type': viz_type
                    })
            
            return diverse_examples
        except Exception as e:
            logger.error(f"Error getting diverse examples: {str(e)}")
            raise

    async def add_snippet_atomic(self, text: str, metadata: Dict[str, Any]) -> None:
        """Atomically add a snippet: embedding, vector store, and metadata store."""
        embedding = EmbeddingService.generate_embedding(text)
        try:
            await self.vector_store.add_visualization(embedding, metadata)
        except Exception as e:
            logger.error(f"Error adding to vector store: {str(e)}")
            raise
        try:
            await self.metadata_service.add_snippet(metadata)
        except Exception as e:
            # Rollback vector store addition if metadata fails (remove last entry)
            if self.vector_store.visualizations:
                self.vector_store.visualizations.pop()
                if self.vector_store.embeddings is not None and len(self.vector_store.embeddings) > 0:
                    self.vector_store.embeddings = self.vector_store.embeddings[:-1]
            logger.error(f"Error adding to metadata store, rolled back vector store: {str(e)}")
            raise

    async def save_vector_store(self) -> None:
        """Save the vector store to disk."""
        try:
            self.vector_store.save(settings.VECTOR_STORE_PATH)
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
            raise

def get_rag_service(
    vector_store: VectorStore = Depends(get_vector_store),
    metadata_service: MetadataService = Depends(get_metadata_service)
) -> RAGService:
    """Get a RAG service instance with vector and metadata stores."""
    return RAGService(vector_store, metadata_service) 