"""Vector store for storing and retrieving visualizations. Embeddings must be precomputed and passed in."""
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config.settings import settings
import json
import logging
from fastapi import Depends
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sqlalchemy.orm import Session
from app.models import SnippetMetadata
from functools import lru_cache

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for storing and retrieving visualizations using Qdrant and DB metadata."""
    def __init__(self, dim: int, collection_name: str = None):
        self.dim = dim
        # Use collection name from settings, fallback to argument, then default
        self.collection_name = settings.VECTOR_STORE_COLLECTION_NAME
        self.client = QdrantClient(host="localhost", port=6333)
        # Create collection if it doesn't exist
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE)
            )

    def add_visualization(self, embedding: np.ndarray, faiss_id: int) -> None:
        """Add a visualization embedding to the Qdrant collection with a given id."""
        if not isinstance(embedding, np.ndarray):
            raise ValueError(f"Embedding must be a numpy ndarray, got {type(embedding)}")
        embedding = embedding.reshape(-1).astype('float32')
        point = qmodels.PointStruct(id=int(faiss_id), vector=embedding.tolist(), payload={})
        self.client.upsert(collection_name=self.collection_name, points=[point])
        logger.info(f"Added vector with id {faiss_id} to Qdrant collection '{self.collection_name}'")

    def save(self, path: str) -> None:
        """No-op for Qdrant (data is persisted automatically)."""
        logger.info("Qdrant persists data automatically; save() is a no-op.")

    def load(self, path: str) -> None:
        """No-op for Qdrant (data is loaded automatically)."""
        logger.info("Qdrant loads data automatically; load() is a no-op.")

    async def get_similar_visualizations(self, query_embedding: np.ndarray, db, limit: int = 5) -> list[dict]:
        """Get similar visualizations for a query embedding. Returns metadata from DB."""
        try:
            logger.info("[get_similar_visualizations] Starting Qdrant search")
            query_vec = np.ascontiguousarray(query_embedding, dtype='float32').reshape(-1).tolist()
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vec,
                limit=limit
            )
            qdrant_ids = [int(hit.id) for hit in search_result]
            logger.info(f"[get_similar_visualizations] Qdrant IDs: {qdrant_ids}")
            # Fetch metadata from DB
            results = db.query(SnippetMetadata).filter(SnippetMetadata.faiss_id.in_(qdrant_ids)).all()
            logger.info(f"[get_similar_visualizations] DB query complete: {len(results)} results")
            # Map faiss_id to metadata for ordering
            meta_map = {m.faiss_id: m for m in results}
            logger.info("[get_similar_visualizations] Mapping complete")
            response = [
                {
                    'metadata': {k: v for k, v in meta_map.get(qid).__dict__.items() if not k.startswith('_sa_instance_state')} if qid in meta_map else None,
                    'similarity': float(hit.score)
                }
                for hit, qid in zip(search_result, qdrant_ids) if qid in meta_map
            ]
            logger.info(f"[get_similar_visualizations] Response ready with {len(response)} items")
            return response
        except Exception as e:
            logger.error(f"[get_similar_visualizations] Error: {str(e)}")
            raise

    def has_snippet_hash(self, snippet_hash: str, db) -> bool:
        """Check if a snippet with the given hash exists in the vector store (via DB)."""
        try:
            existing = db.query(SnippetMetadata).filter(SnippetMetadata.snippet_hash == snippet_hash).first()
            return existing is not None
        except Exception as e:
            logger.error(f"Error checking snippet hash: {str(e)}")
            return False

    def _compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        return float(np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))

@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    """Get the global vector store instance."""
    _vector_store = VectorStore(dim=settings.VECTOR_STORE_DIMENSION)
    return _vector_store