from typing import List, Dict, Any
import logging
from .vector_store import get_vector_store
from app.config.settings import settings

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.vector_store = get_vector_store()
        try:
            # Try to load existing vector store
            self.vector_store.load(settings.VECTOR_STORE_PATH)
            logger.info("Successfully loaded vector store", extra={
                "action": "init_rag_service",
                "path": settings.VECTOR_STORE_PATH
            })
        except Exception as e:
            logger.warning("Could not load vector store, will create new one", extra={
                "action": "init_rag_service",
                "error": str(e),
                "error_type": type(e).__name__
            })
    
    def prepare_llm_prompt(self, user_prompt: str, config_json: Dict[str, Any]) -> str:
        """Prepare an augmented prompt for the LLM using RAG."""
        # Search for similar visualizations
        similar_viz = self.vector_store.search(user_prompt, top_k=2)
        
        # Prepare examples from similar visualizations
        examples_text = ""
        if similar_viz:
            examples_text = "\n\n".join([
                f"Example {i+1}:\n"
                f"HTML: {viz['metadata']['html']}\n"
                f"Config: {viz['metadata']['config']}"
                for i, viz in enumerate(similar_viz)
            ])
        
        # Construct the augmented prompt
        prompt = (
            "You are a 3D visualization generator. Your task is to create an HTML visualization "
            "based on the user's request and configuration.\n\n"
        )
        
        if examples_text:
            prompt += (
                "Here are some similar examples that might help guide your generation:\n"
                f"{examples_text}\n\n"
            )
        
        prompt += (
            f"User Request: {user_prompt}\n"
            f"Configuration: {config_json}\n\n"
            "Please generate an HTML visualization that matches the user's request "
            "and follows the provided configuration. Use Three.js for 3D rendering."
        )
        
        return prompt
    
    def add_gold_standard(self, html: str, config: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Add a gold standard visualization to the vector store."""
        try:
            if metadata is None:
                metadata = {}
            
            # Combine metadata
            full_metadata = {
                'html': html,
                'config': config,
                **metadata
            }
            
            # Add to vector store
            self.vector_store.add_visualization(html, full_metadata)
            
            # Save the updated vector store
            self.vector_store.save(settings.VECTOR_STORE_PATH)
            
            logger.info("Successfully added gold standard", extra={
                "action": "add_gold_standard",
                "has_config": bool(config),
                "has_metadata": bool(metadata)
            })
        except Exception as e:
            logger.error("Error adding gold standard", extra={
                "action": "add_gold_standard",
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
    
    def get_similar_visualizations(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Get similar visualizations for a query."""
        return self.vector_store.search(query, top_k=top_k)

# Global RAG service instance
rag_service = RAGService()

def get_rag_service() -> RAGService:
    """Get the global RAG service instance."""
    return rag_service 