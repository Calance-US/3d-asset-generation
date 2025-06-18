"""Vector store for storing and retrieving visualizations. Embeddings must be precomputed and passed in."""
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config.settings import settings
import json
import logging
from fastapi import Depends
import faiss
from sqlalchemy.orm import Session
from app.models import SnippetMetadata

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for storing and retrieving visualizations using FAISS IndexIDMap and DB metadata."""
    
    def __init__(self, dim: int):
        self.dim = dim
        self.faiss_index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
    
    def add_visualization(self, embedding: np.ndarray, faiss_id: int) -> None:
        """Add a visualization embedding to the FAISS index with a given faiss_id."""
        if not isinstance(embedding, np.ndarray):
            raise ValueError(f"Embedding must be a numpy ndarray, got {type(embedding)}")
        embedding = embedding.reshape(1, -1)
        ids = np.array([faiss_id], dtype=np.int64)
        self.faiss_index.add_with_ids(embedding, ids)
    
    def save(self, path: str) -> None:
        """Save the FAISS index to disk."""
        try:
            faiss.write_index(self.faiss_index, path + '.faiss')
            logger.info(f"Successfully saved FAISS index to {path + '.faiss'}")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
            raise
    
    def load(self, path: str) -> None:
        """Load the FAISS index from disk."""
        try:
            import os
            faiss_path = path + '.faiss'
            if not os.path.exists(faiss_path):
                raise FileNotFoundError(f"FAISS index file not found: {faiss_path}")
            self.faiss_index = faiss.read_index(faiss_path)
            logger.info(f"Loaded FAISS index from {faiss_path}")
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")
            raise
    
    async def get_similar_visualizations(self, query_embedding: np.ndarray, db: Session, limit: int = 5) -> list[dict]:
        """Get similar visualizations for a query embedding. Returns metadata from DB."""
        try:
            if self.faiss_index is None or self.faiss_index.ntotal == 0:
                return []
            D, I = self.faiss_index.search(query_embedding.reshape(1, -1), limit)
            faiss_ids = [int(i) for i in I[0] if i != -1]
            # Fetch metadata from DB
            results = db.query(SnippetMetadata).filter(SnippetMetadata.faiss_id.in_(faiss_ids)).all()
            # Map faiss_id to metadata for ordering
            meta_map = {m.faiss_id: m for m in results}
            return [
                {
                    'metadata': meta_map.get(faiss_id),
                    'similarity': float(D[0][j])
                }
                for j, faiss_id in enumerate(faiss_ids) if faiss_id in meta_map
            ]
        except Exception as e:
            logger.error(f"Error getting similar visualizations: {str(e)}")
            raise

    def has_snippet_hash(self, snippet_hash: str, db: Session) -> bool:
        """Check if a snippet with the given hash exists in the vector store."""
        try:
            existing = db.query(SnippetMetadata).filter(SnippetMetadata.snippet_hash == snippet_hash).first()
            return existing is not None
        except Exception as e:
            logger.error(f"Error checking snippet hash: {str(e)}")
            return False

    def _compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        return float(np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))

# Global vector store instance
_vector_store = VectorStore(dim=settings.VECTOR_STORE_DIMENSION)

def get_vector_store() -> VectorStore:
    """Get the global vector store instance."""
    return _vector_store 