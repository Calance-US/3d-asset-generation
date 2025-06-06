import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from sentence_transformers import SentenceTransformer
import logging
from sqlalchemy.orm import Session
import faiss
from ..database.db_config import SessionLocal
from ..models import Prompt
from app.database.database import get_prompts, get_db
from app.config.settings import settings
from .prompt_generator import PromptGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptSelector:
    def __init__(self):
        """Initialize the prompt selector with FAISS index and sentence transformer."""
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.prompts = []
        self.index = None
        self.db = None
        self.prompt_generator = PromptGenerator()
        self.initialize_index()
        
        # Default prompts for each subject and provider
        self.default_prompts = {
            "physics": {
                "openai": "You are a physics expert. Create a 3D visualization for the following concept: {topic}",
                "gemini": "As a physics expert, generate a 3D visualization for: {topic}",
                "ollama": "Physics expert here. Visualize in 3D: {topic}"
            },
            "chemistry": {
                "openai": "You are a chemistry expert. Create a 3D visualization for the following concept: {topic}",
                "gemini": "As a chemistry expert, generate a 3D visualization for: {topic}",
                "ollama": "Chemistry expert here. Visualize in 3D: {topic}"
            },
            "biology": {
                "openai": "You are a biology expert. Create a 3D visualization for the following concept: {topic}",
                "gemini": "As a biology expert, generate a 3D visualization for: {topic}",
                "ollama": "Biology expert here. Visualize in 3D: {topic}"
            },
            "mathematics": {
                "openai": "You are a mathematics expert. Create a 3D visualization for the following concept: {topic}",
                "gemini": "As a mathematics expert, generate a 3D visualization for: {topic}",
                "ollama": "Mathematics expert here. Visualize in 3D: {topic}"
            }
        }
    
    def initialize_index(self):
        """Initialize or update the FAISS index with current prompts."""
        try:
            # Get all prompts from database
            self.db = next(get_db())
            prompts = get_prompts(self.db)
            
            logger.info(f"Found {len(prompts)} prompts in database")
            for prompt in prompts:
                logger.info(f"Prompt: id={prompt.id}, subject={prompt.subject}, topic={prompt.topic}")
            
            if not prompts:
                logger.warning("No prompts found in database")
                return
            
            # Prepare text for embedding
            texts = []
            for prompt in prompts:
                # Combine relevant fields for semantic search
                text = f"Subject: {prompt.subject}\n"
                text += f"Topic: {prompt.topic}\n"
                text += f"Content: {prompt.content}\n"
                if prompt.category:
                    text += f"Category: {prompt.category}\n"
                if prompt.tags:
                    text += f"Tags: {', '.join(tag.name for tag in prompt.tags)}\n"
                texts.append(text)
                logger.info(f"Prepared text for embedding: {text[:100]}...")
            
            # Generate embeddings
            logger.info("Generating embeddings...")
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            embeddings = embeddings.astype('float32')
            
            # Normalize embeddings to unit vectors for better similarity search
            faiss.normalize_L2(embeddings)
            
            # Create FAISS index using inner product (cosine similarity)
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            self.index.add(embeddings)
            
            # Store prompts for reference
            self.prompts = list(prompts)
            
            logger.info(f"Successfully initialized FAISS index with {len(prompts)} prompts")
            
        except Exception as e:
            logger.error(f"Error initializing FAISS index: {str(e)}")
            self.index = None
            self.prompts = []
            if self.db:
                self.db.close()
                self.db = None
    
    def select_prompt(self, user_query: str, subject: str = None) -> tuple[str, str]:
        """
        Select the most appropriate prompt based on user query using semantic search.
        
        Args:
            user_query: The user's query string
            subject: Optional subject to filter topics by
            
        Returns:
            Tuple[str, str]: (subject, topic) of the selected prompt
        """
        logger.info(f"Selecting prompt for query: {user_query}, subject: {subject}")
        
        if not self.prompts or not self.index:
            logger.info("No prompts available or index not initialized, using generic prompt")
            return subject or 'physics', 'generic'
        
        try:
            # Get query embedding and normalize it
            query_embedding = self.model.encode([user_query])[0]
            query_embedding = query_embedding.astype('float32').reshape(1, -1)
            faiss.normalize_L2(query_embedding)  # Normalize query vector
            
            # Filter prompts by subject if provided
            filtered_indices = []
            if subject:
                filtered_indices = [i for i, p in enumerate(self.prompts) 
                                  if p.subject.lower() == subject.lower()]
                logger.info(f"Found {len(filtered_indices)} prompts for subject {subject}")
                if not filtered_indices:
                    logger.info(f"No prompts found for subject {subject}, using generic prompt")
                    return subject or 'physics', 'generic'
            
            # Search in FAISS index
            k = min(5, len(self.prompts))  # Get top 5 results or all if less than 5
            if filtered_indices:
                # Create a subset of the index for the filtered prompts
                filtered_index = faiss.IndexFlatIP(self.index.d)  # Use inner product for filtered index too
                filtered_vectors = self.index.reconstruct_batch(filtered_indices)
                faiss.normalize_L2(filtered_vectors)  # Normalize filtered vectors
                filtered_index.add(filtered_vectors)
                similarities, indices = filtered_index.search(query_embedding, k)
                # Map indices back to original prompt indices
                indices = [filtered_indices[i] for i in indices[0]]
            else:
                similarities, indices = self.index.search(query_embedding, k)
                indices = indices[0]
            
            # Get the best matches
            best_matches = []
            for i, idx in enumerate(indices):
                idx = int(idx)  # Convert to int to ensure proper indexing
                similarity = float(similarities[0][i])  # Convert to float for score calculation
                
                # Skip invalid indices
                if idx >= len(self.prompts):
                    continue
                
                # Similarity is already in [0, 1] range for normalized vectors
                # Higher similarity means better match
                prompt = self.prompts[idx]
                best_matches.append((prompt, similarity))
            
            if not best_matches:
                logger.info("No valid matches found, using generic prompt")
                return subject or 'physics', 'generic'
            
            # Sort matches by similarity in descending order
            best_matches.sort(key=lambda x: x[1], reverse=True)
            
            # Log all matches for debugging
            logger.info("Top matches:")
            for prompt, similarity in best_matches:
                logger.info(f"Match: {prompt.topic} (similarity: {similarity:.3f}, subject: {prompt.subject})")
            
            # Get the best match
            best_prompt, best_similarity = best_matches[0]
            
            # Use a lower threshold for better matching
            if best_similarity > 0.3:  # Threshold for cosine similarity
                logger.info(f"Using topic-specific prompt: {best_prompt.topic} (similarity: {best_similarity:.3f})")
                return best_prompt.subject, best_prompt.topic
            
            # If no good match found, try to infer subject from query
            if not subject:
                # Check if query contains subject-related keywords
                subject_keywords = {
                    'physics': ['physics', 'mechanical', 'electrical', 'force', 'motion', 'energy'],
                    'chemistry': ['chemistry', 'chemical', 'atomic', 'molecular', 'reaction', 'atom', 'structure'],
                    'biology': ['biology', 'biological', 'cell', 'organism', 'life'],
                    'mathematics': ['mathematics', 'math', 'algebra', 'geometry', 'calculus']
                }
                
                for subj, keywords in subject_keywords.items():
                    if any(keyword in user_query.lower() for keyword in keywords):
                        logger.info(f"Inferred subject from query: {subj}")
                        return subj, 'generic'
            
            # If still no match, return generic prompt for the subject
            logger.info(f"Using generic prompt for subject: {subject}")
            return subject or 'physics', 'generic'
            
        except Exception as e:
            logger.error(f"Error in select_prompt: {str(e)}")
            # Fallback to generic prompt on error
            return subject or 'physics', 'generic'
    
    def get_prompt_content(self, subject: str, topic: str, user_topic: str = None) -> str:
        """
        Get the content of a specific prompt.
        
        Args:
            subject: The subject of the prompt
            topic: The topic of the prompt
            user_topic: Optional user topic for logging
            
        Returns:
            str: The prompt content
        """
        logger.info(f"Getting prompt content for subject: {subject}, topic: {topic}, user_topic: {user_topic}")
        
        try:
            # Find the prompt in our stored prompts
            for prompt in self.prompts:
                if prompt.subject.lower() == subject.lower() and prompt.topic.lower() == topic.lower():
                    return prompt.content
            
            # If not found, generate a new prompt using the template
            logger.info(f"Specific prompt not found, generating new prompt for {subject}")
            return self.prompt_generator.generate_from_topic(
                topic=user_topic or topic,
                subject=subject,
                education_level="High School"  # Default education level
            )
            
        except Exception as e:
            logger.error(f"Error getting prompt content: {str(e)}")
            return f"Create a 3D visualization for {user_topic or topic} in {subject}."

    def get_prompt(self, subject: str, provider: str, topic: str) -> str:
        """
        Get the appropriate prompt for the given subject, provider, and topic.
        
        Args:
            subject: The subject area (physics, chemistry, biology, mathematics)
            provider: The AI provider (openai, gemini, ollama)
            topic: The specific topic to visualize
            
        Returns:
            The formatted prompt string
        """
        if subject not in self.default_prompts:
            raise ValueError(f"Unknown subject: {subject}")
        if provider not in self.default_prompts[subject]:
            raise ValueError(f"Unknown provider: {provider}")
            
        return self.default_prompts[subject][provider].format(topic=topic)
    
    def __del__(self):
        """Clean up database session."""
        self.db.close() 