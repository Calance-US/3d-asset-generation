import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from sentence_transformers import SentenceTransformer
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptSelector:
    def __init__(self):
        logger.info("Initializing PromptSelector...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        self.embeddings_dir = self.prompts_dir / "embeddings"
        self.topics_file = self.prompts_dir / "topics.json"
        self.embeddings_file = self.embeddings_dir / "topics.npy"
        
        # Create embeddings directory if it doesn't exist
        self.embeddings_dir.mkdir(exist_ok=True)
        
        # Load or create embeddings
        self.topics = self._load_topics()
        logger.info(f"Loaded {len(self.topics)} topics from topics.json")
        self.embeddings = self._load_or_create_embeddings()
        logger.info("Embeddings loaded/created successfully")
        
    def _load_topics(self) -> List[Dict]:
        """Load topics from JSON file."""
        logger.info(f"Loading topics from {self.topics_file}")
        with open(self.topics_file, 'r') as f:
            topics = json.load(f)
        logger.info(f"Loaded topics: {[topic['title'] for topic in topics]}")
        return topics
    
    def _load_or_create_embeddings(self) -> np.ndarray:
        """Load existing embeddings or create new ones."""
        if self.embeddings_file.exists():
            logger.info(f"Loading existing embeddings from {self.embeddings_file}")
            return np.load(self.embeddings_file)
        
        logger.info("Creating new embeddings for topics")
        # Create embeddings for all topics
        titles = [topic['title'] for topic in self.topics]
        embeddings = self.model.encode(titles)
        
        # Save embeddings
        logger.info(f"Saving embeddings to {self.embeddings_file}")
        np.save(self.embeddings_file, embeddings)
        return embeddings
    
    def select_prompt(self, user_query: str, subject: str = None) -> Tuple[str, str]:
        """
        Select the most appropriate prompt based on user query.
        
        Args:
            user_query: The user's query string
            subject: Optional subject to filter topics by
            
        Returns:
            Tuple[str, str]: (subject, filename) of the selected prompt
        """
        logger.info(f"Selecting prompt for query: {user_query}, subject: {subject}")
        
        # Filter topics by subject if provided
        filtered_topics = self.topics
        if subject:
            filtered_topics = [topic for topic in self.topics if topic['subject'] == subject]
            logger.info(f"Filtered topics for subject {subject}: {[topic['title'] for topic in filtered_topics]}")
        
        if not filtered_topics:
            logger.info(f"No topics found for subject {subject}, using generic prompt")
            return subject or 'physics', f"{subject or 'physics'}/generic.txt"
        
        # Create embeddings for filtered topics
        titles = [topic['title'] for topic in filtered_topics]
        topic_embeddings = self.model.encode(titles)
        
        # Embed the user query
        query_embedding = self.model.encode([user_query])[0]
        
        # Calculate cosine similarities
        similarities = np.dot(topic_embeddings, query_embedding) / (
            np.linalg.norm(topic_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get the best match
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        best_topic = filtered_topics[best_idx]
        
        logger.info(f"Best matching topic: {best_topic['title']} (score: {best_score:.3f})")
        
        # Lower threshold to 0.6 for better matching
        if best_score > 0.6:
            logger.info(f"Using topic-specific prompt: {best_topic['file']}")
            return best_topic['subject'], best_topic['file']
        
        logger.info("Cosine similarity below threshold, falling back to keyword search")
        # Fallback to keyword-based search with improved matching
        query_lower = user_query.lower()
        for topic in filtered_topics:
            # Check if the topic title contains the query or vice versa
            topic_lower = topic['title'].lower()
            if (query_lower in topic_lower or topic_lower in query_lower or
                any(word in topic_lower for word in query_lower.split())):
                logger.info(f"Found keyword match: {topic['title']}")
                return topic['subject'], topic['file']
        
        # If no match found, return generic prompt for the subject
        logger.info(f"Using generic prompt for subject: {subject}")
        return subject or 'physics', f"{subject or 'physics'}/generic.txt"
    
    def get_prompt_content(self, subject: str, filename: str, topic: str = None) -> str:
        """Get the content of the selected prompt file."""
        logger.info(f"Getting prompt content for subject: {subject}, file: {filename}, topic: {topic}")
        
        # First try the exact file path
        prompt_path = self.prompts_dir / subject / filename
        logger.info(f"Trying path: {prompt_path}")
        
        if prompt_path.exists():
            logger.info(f"Found specific prompt file: {prompt_path}")
            content = prompt_path.read_text()
            # Format the content with the topic if needed
            if topic and '{topic}' in content:
                logger.info(f"Formatting prompt with topic: {topic}")
                try:
                    content = content.format(topic=topic)
                except Exception as e:
                    logger.error(f"Error formatting prompt: {e}")
                    # If formatting fails, return unformatted content
                    return content
            return content
        
        # If not found, try without the subject prefix in filename
        if filename.startswith(f"{subject}_"):
            filename = filename[len(subject)+1:]
            prompt_path = self.prompts_dir / subject / filename
            logger.info(f"Trying path without subject prefix: {prompt_path}")
            
            if prompt_path.exists():
                logger.info(f"Found specific prompt file: {prompt_path}")
                content = prompt_path.read_text()
                # Format the content with the topic if needed
                if topic and '{topic}' in content:
                    logger.info(f"Formatting prompt with topic: {topic}")
                    try:
                        content = content.format(topic=topic)
                    except Exception as e:
                        logger.error(f"Error formatting prompt: {e}")
                        # If formatting fails, return unformatted content
                        return content
                return content
        
        logger.info(f"Specific prompt not found, trying generic prompt for {subject}")
        # Fallback to generic prompt
        generic_path = self.prompts_dir / subject / "generic.txt"
        if generic_path.exists():
            logger.info(f"Using generic prompt: {generic_path}")
            content = generic_path.read_text()
            # Format the content with the topic if needed
            if topic and '{topic}' in content:
                logger.info(f"Formatting prompt with topic: {topic}")
                try:
                    content = content.format(topic=topic)
                except Exception as e:
                    logger.error(f"Error formatting prompt: {e}")
                    # If formatting fails, return unformatted content
                    return content
            return content
        
        logger.info("No prompts found, using default prompt")
        # Ultimate fallback to default prompt
        return """Create an interactive 3D visualization using Three.js that demonstrates the concept.
The visualization should be educational and include:
1. Clear labels and annotations
2. Interactive elements for user engagement
3. Proper lighting and camera controls
4. Responsive design
5. Scientific accuracy
6. Visual clarity and intuitive understanding

Return only the complete HTML code with embedded Three.js.""" 