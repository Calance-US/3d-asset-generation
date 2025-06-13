import faiss
import numpy as np
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import logging
from sentence_transformers import SentenceTransformer
from app.config.settings import settings

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, dimension: int = 384):
        """Initialize the vector store with FAISS index."""
        try:
            self.dimension = dimension
            self.index = faiss.IndexFlatL2(dimension)
            self.embeddings = []
            self.metadata = []
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Successfully initialized vector store", extra={
                "action": "init_vector_store",
                "dimension": dimension,
                "model": "all-MiniLM-L6-v2"
            })
        except Exception as e:
            logger.error("Error initializing vector store", extra={
                "action": "init_vector_store",
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
        
    def add_visualization(self, html: str, metadata: Dict[str, Any]) -> int:
        """Add a visualization to the vector store."""
        try:
            if not html:
                raise ValueError("HTML content cannot be empty")
            
            # Create a rich text representation including topic and subject
            topic = metadata.get('topic', '')
            subject = metadata.get('subject', '')
            rich_text = f"Topic: {topic}\nSubject: {subject}\nContent: {html}"
            
            # Generate embedding from rich text
            embedding = self.model.encode([rich_text])[0]
            
            # Validate embedding
            if embedding.shape[0] != self.dimension:
                raise ValueError(f"Embedding dimension mismatch. Expected {self.dimension}, got {embedding.shape[0]}")
            
            # Convert to float32 and reshape for FAISS
            embedding_array = np.array([embedding], dtype=np.float32)
            
            # Add to FAISS index
            self.index.add(embedding_array)
            
            # Store metadata and embedding
            self.metadata.append(metadata)
            self.embeddings.append(embedding)
            
            logger.info("Successfully added visualization to vector store", extra={
                "action": "add_visualization",
                "metadata_keys": list(metadata.keys()),
                "has_topic": bool(topic),
                "has_subject": bool(subject)
            })
            
            return len(self.metadata) - 1
            
        except Exception as e:
            logger.error("Error adding visualization to vector store", extra={
                "action": "add_visualization",
                "error": str(e),
                "error_type": type(e).__name__,
                "html_length": len(html) if html else 0,
                "metadata_keys": list(metadata.keys()) if metadata else []
            })
            raise
    
    def search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Search for similar visualizations."""
        try:
            if not query:
                raise ValueError("Search query cannot be empty")
            
            # Create a rich text representation of the query
            rich_query = f"Query: {query}"
            
            # Generate query embedding
            query_embedding = self.model.encode([rich_query])[0]
            
            # Validate embedding
            if query_embedding.shape[0] != self.dimension:
                raise ValueError(f"Query embedding dimension mismatch. Expected {self.dimension}, got {query_embedding.shape[0]}")
            
            # Convert to float32 and reshape for FAISS
            query_array = np.array([query_embedding], dtype=np.float32)
            
            # Search in FAISS
            distances, indices = self.index.search(query_array, top_k)
            
            # Return results with metadata
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx != -1:  # FAISS returns -1 for empty slots
                    results.append({
                        'metadata': self.metadata[idx],
                        'distance': float(distance),
                        'embedding': self.embeddings[idx] if isinstance(self.embeddings[idx], list) else self.embeddings[idx].tolist()
                    })
            
            logger.info("Successfully searched vector store", extra={
                "action": "search",
                "query_length": len(query),
                "results_count": len(results)
            })
            
            return results
            
        except Exception as e:
            logger.error("Error searching vector store", extra={
                "action": "search",
                "error": str(e),
                "error_type": type(e).__name__,
                "query_length": len(query) if query else 0
            })
            raise
    
    def save(self, path: str):
        """Save the vector store to disk."""
        try:
            save_path = Path(path)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, str(save_path / "index.faiss"))
            
            # Save metadata and embeddings
            with open(save_path / "metadata.json", "w") as f:
                json.dump(self.metadata, f)
            
            np.save(save_path / "embeddings.npy", np.array(self.embeddings))
            
            logger.info("Successfully saved vector store", extra={
                "action": "save",
                "path": str(save_path),
                "metadata_count": len(self.metadata),
                "embeddings_count": len(self.embeddings)
            })
            
        except Exception as e:
            logger.error("Error saving vector store", extra={
                "action": "save",
                "error": str(e),
                "error_type": type(e).__name__,
                "path": str(path)
            })
            raise
    
    def load(self, path: str):
        """Load the vector store from disk."""
        try:
            load_path = Path(path)
            
            # Check if files exist
            if not (load_path / "index.faiss").exists():
                logger.warning("Vector store files not found, initializing new store", extra={
                    "action": "load",
                    "path": str(load_path)
                })
                return
            
            # Load FAISS index
            self.index = faiss.read_index(str(load_path / "index.faiss"))
            
            # Load metadata and embeddings
            with open(load_path / "metadata.json", "r") as f:
                self.metadata = json.load(f)
            
            self.embeddings = np.load(load_path / "embeddings.npy").tolist()
            
            logger.info("Successfully loaded vector store", extra={
                "action": "load",
                "path": str(load_path),
                "metadata_count": len(self.metadata),
                "embeddings_count": len(self.embeddings)
            })
            
        except Exception as e:
            logger.error("Error loading vector store", extra={
                "action": "load",
                "error": str(e),
                "error_type": type(e).__name__,
                "path": str(path)
            })
            raise

    def delete_visualization(self, index: int) -> bool:
        """Delete a visualization from the vector store."""
        try:
            if index < 0 or index >= len(self.metadata):
                raise ValueError(f"Invalid index: {index}")
            
            # Create a new index without the deleted entry
            new_index = faiss.IndexFlatL2(self.dimension)
            
            # Add all embeddings except the one to delete
            for i, embedding in enumerate(self.embeddings):
                if i != index:
                    embedding_array = np.array([embedding], dtype=np.float32)
                    new_index.add(embedding_array)
            
            # Update the index
            self.index = new_index
            
            # Remove from metadata and embeddings
            self.metadata.pop(index)
            self.embeddings.pop(index)
            
            logger.info("Successfully deleted visualization from vector store", extra={
                "action": "delete_visualization",
                "index": index,
                "remaining_count": len(self.metadata)
            })
            
            return True
            
        except Exception as e:
            logger.error("Error deleting visualization from vector store", extra={
                "action": "delete_visualization",
                "error": str(e),
                "error_type": type(e).__name__,
                "index": index
            })
            raise

# Global vector store instance
vector_store = VectorStore()

def get_vector_store() -> VectorStore:
    """Get the global vector store instance."""
    return vector_store 