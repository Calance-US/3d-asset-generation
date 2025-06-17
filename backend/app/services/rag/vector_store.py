"""Vector store for storing and retrieving visualizations. Embeddings must be precomputed and passed in."""
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config.settings import settings
import json
import logging
from fastapi import Depends
import faiss

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for storing and retrieving visualizations."""
    
    def __init__(self):
        self.visualizations: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.faiss_index = None  # Internal FAISS index
    
    def _ensure_faiss_index(self):
        if self.embeddings is not None and len(self.embeddings) > 0:
            dim = self.embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatL2(dim)
            self.faiss_index.add(self.embeddings)
        else:
            self.faiss_index = None
    
    async def add_visualization(self, embedding: np.ndarray, metadata: Dict[str, Any]) -> None:
        """Add a visualization to the store. Embedding must be precomputed and passed in."""
        try:
            if not isinstance(embedding, np.ndarray):
                raise ValueError(f"Embedding must be a numpy ndarray, got {type(embedding)}")
            self.visualizations.append({
                'metadata': metadata,
                'embedding': embedding
            })
            if self.embeddings is None:
                self.embeddings = embedding.reshape(1, -1)
            else:
                self.embeddings = np.vstack([self.embeddings, embedding])
            # Add to FAISS
            if self.faiss_index is None:
                self._ensure_faiss_index()
            else:
                self.faiss_index.add(embedding.reshape(1, -1))
            logger.info("Successfully added visualization to vector store (FAISS-backed)")
        except Exception as e:
            logger.error(f"Error adding visualization to vector store: {str(e)}")
            raise
    
    async def get_similar_visualizations(self, query_embedding: np.ndarray, limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar visualizations for a query embedding. Embedding must be precomputed and passed in."""
        try:
            if self.faiss_index is None or self.embeddings is None or len(self.embeddings) == 0:
                return []
            D, I = self.faiss_index.search(query_embedding.reshape(1, -1), limit)
            return [
                {
                    'metadata': self.visualizations[i]['metadata'],
                    'similarity': float(-D[0][j])  # Negate for L2 distance to get similarity
                }
                for j, i in enumerate(I[0]) if i >= 0 and i < len(self.visualizations)
            ]
        except Exception as e:
            logger.error(f"Error getting similar visualizations: {str(e)}")
            raise
    
    def save(self, path: str) -> None:
        """Save the vector store to disk."""
        try:
            # Convert embeddings to list for JSON serialization
            data = {
                'visualizations': [
                    {
                        'metadata': viz['metadata'],
                        'embedding': viz['embedding'].tolist()
                    }
                    for viz in self.visualizations
                ]
            }
            # Save to file
            with open(path, 'w') as f:
                json.dump(data, f)
            # Save FAISS index
            if self.faiss_index is not None:
                faiss.write_index(self.faiss_index, path + '.faiss')
            logger.info(f"Successfully saved vector store to {path} and FAISS index to {path + '.faiss'}")
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
            raise
    
    def load(self, path: str) -> None:
        """Load the vector store from disk."""
        try:
            # Load from file
            with open(path, 'r') as f:
                data = json.load(f)
            # Convert embeddings back to numpy arrays
            self.visualizations = [
                {
                    'metadata': viz['metadata'],
                    'embedding': np.array(viz['embedding'])
                }
                for viz in data['visualizations']
            ]
            # Update embeddings matrix
            if self.visualizations:
                self.embeddings = np.vstack([viz['embedding'] for viz in self.visualizations])
            else:
                self.embeddings = None
            # Load or rebuild FAISS index
            import os
            faiss_path = path + '.faiss'
            if os.path.exists(faiss_path):
                self.faiss_index = faiss.read_index(faiss_path)
            else:
                self._ensure_faiss_index()
            logger.info(f"Successfully loaded vector store from {path} and FAISS index from {faiss_path if os.path.exists(faiss_path) else '[rebuilt]'}")
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            raise

    def has_snippet_hash(self, snippet_hash: str) -> bool:
        """Check if a snippet with the given hash exists in the vector store."""
        return any(viz['metadata'].get('snippet_hash') == snippet_hash for viz in self.visualizations)

    def _compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        return float(np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))

# Global vector store instance
_vector_store = VectorStore()

def get_vector_store() -> VectorStore:
    """Get the global vector store instance."""
    return _vector_store 