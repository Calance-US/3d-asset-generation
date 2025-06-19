from datetime import datetime

import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from app.config.logging_config import logger

from ..database.db_config import SessionLocal
from ..models import Prompt
from .prompt_generator import PromptGenerator


class PromptSelector:
    def __init__(self):
        """Initialize the prompt selector with a sentence transformer model."""
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.db = SessionLocal()
            self.prompts = []
            self.index = None
            self.prompt_generator = PromptGenerator()
            self.initialize_index()
            self.generate_embeddings_for_prompts()  # Generate embeddings for existing prompts
            logger.info("PromptSelector initialized", extra={"action": "init"})
        except Exception as e:
            logger.error(
                "Failed to initialize PromptSelector",
                extra={"action": "init", "error": str(e)},
            )
            raise

        # Default prompts for each subject and provider
        self.default_prompts = {
            "physics": {
                "openai": "You are a physics expert. Create a 3D visualization for the following concept: {topic}",
                "gemini": "As a physics expert, generate a 3D visualization for: {topic}",
                "ollama": "Physics expert here. Visualize in 3D: {topic}",
            },
            "chemistry": {
                "openai": "You are a chemistry expert. Create a 3D visualization for the following concept: {topic}",
                "gemini": "As a chemistry expert, generate a 3D visualization for: {topic}",
                "ollama": "Chemistry expert here. Visualize in 3D: {topic}",
            },
            "biology": {
                "openai": "You are a biology expert. Create a 3D visualization for the following concept: {topic}",
                "gemini": "As a biology expert, generate a 3D visualization for: {topic}",
                "ollama": "Biology expert here. Visualize in 3D: {topic}",
            },
            "mathematics": {
                "openai": "You are a mathematics expert. Create a 3D visualization for the following concept: {topic}",
                "gemini": "As a mathematics expert, generate a 3D visualization for: {topic}",
                "ollama": "Mathematics expert here. Visualize in 3D: {topic}",
            },
        }

    def initialize_index(self) -> None:
        """Initialize the FAISS index with existing prompts."""
        try:
            self.prompts = self.db.query(Prompt).all()
            if not self.prompts:
                logger.info(
                    "No prompts found in database", extra={"action": "initialize_index"}
                )
                return

            # Filter out prompts without embeddings
            prompts_with_embeddings = [
                p for p in self.prompts if p.embedding is not None
            ]
            if not prompts_with_embeddings:
                logger.info(
                    "No prompts with embeddings found",
                    extra={"action": "initialize_index"},
                )
                return

            # Get the dimension from the first prompt with an embedding
            dimension = len(prompts_with_embeddings[0].embedding)
            self.index = faiss.IndexFlatL2(dimension)

            # Convert embeddings to numpy array and add to index
            embeddings = np.array(
                [p.embedding for p in prompts_with_embeddings], dtype=np.float32
            )
            self.index.add(embeddings)

            logger.info(
                "FAISS index initialized",
                extra={
                    "action": "initialize_index",
                    "num_prompts": len(prompts_with_embeddings),
                    "dimension": dimension,
                },
            )
        except Exception as e:
            logger.error(
                "Failed to initialize FAISS index",
                extra={"action": "initialize_index", "error": str(e)},
            )
            raise

    def select_prompt(
        self, user_query: str, subject: str | None = None
    ) -> tuple[str, str]:
        """Select the most appropriate prompt based on the user query and subject."""
        try:
            if not self.index or not self.prompts:
                logger.warning(
                    "Index not initialized or no prompts available",
                    extra={"action": "select_prompt", "reason": "no_index_or_prompts"},
                )
                return "physics", "generic"  # Return default values

            # Get query embedding
            query_embedding = self.model.encode([user_query], convert_to_numpy=True)[0]
            query_embedding = torch.tensor(query_embedding).float().reshape(1, -1)

            # Define number of results to return
            k = min(5, len(self.prompts))  # Get top 5 results or all if less than 5

            # Get embedding dimension
            dimension = len(query_embedding[0])

            # Search for similar prompts
            if subject:
                # Filter prompts by subject
                filtered_prompts = [
                    p for p in self.prompts if p.subject.lower() == subject.lower()
                ]
                if not filtered_prompts:
                    logger.info(
                        "No prompts found for subject",
                        extra={
                            "action": "select_prompt",
                            "subject": subject,
                            "reason": "no_subject_prompts",
                        },
                    )
                    return (
                        subject.lower(),
                        "generic",
                    )  # Return the requested subject with generic type

                # Create mapping of filtered indices to original indices
                filtered_indices = [
                    i
                    for i, p in enumerate(self.prompts)
                    if p.subject.lower() == subject.lower()
                ]

                # Create filtered index
                filtered_index = faiss.IndexFlatIP(dimension)
                filtered_vectors = np.array([p.embedding for p in filtered_prompts])
                faiss.normalize_L2(filtered_vectors)  # Normalize filtered vectors
                filtered_index.add(n=filtered_vectors.shape[0], x=filtered_vectors)

                # Search in filtered index
                distances = np.zeros((1, k), dtype=np.float32)
                labels = np.zeros((1, k), dtype=np.int64)
                filtered_index.search(
                    n=1,
                    x=query_embedding.numpy(),
                    k=k,
                    distances=distances,
                    labels=labels,
                )

                # Map indices back to original prompt indices
                indices = [filtered_indices[i] for i in labels[0]]
            else:
                # Search in full index
                distances = np.zeros((1, k), dtype=np.float32)
                labels = np.zeros((1, k), dtype=np.int64)
                self.index.search(
                    n=1,
                    x=query_embedding.numpy(),
                    k=k,
                    distances=distances,
                    labels=labels,
                )
                indices = labels[0]

            # Get the best matches
            best_matches = []
            for i, idx in enumerate(indices):
                idx = int(idx)  # Convert to int to ensure proper indexing
                similarity = float(
                    distances[0][i]
                )  # Convert to float for score calculation

                # Skip invalid indices
                if idx >= len(self.prompts):
                    continue

                prompt = self.prompts[idx]
                score = similarity * 0.7  # Weight similarity score

                # Add subject match bonus
                if subject and prompt.subject.lower() == subject.lower():
                    score += 0.3

                best_matches.append((prompt, score))

            # Sort by score and get the best match
            best_matches.sort(key=lambda x: x[1], reverse=True)
            if best_matches:
                best_prompt = best_matches[0][0]
                logger.info(
                    "Selected prompt",
                    extra={
                        "action": "select_prompt",
                        "prompt_id": best_prompt.id,
                        "subject": best_prompt.subject,
                        "topic": best_prompt.topic,
                        "score": best_matches[0][1],
                    },
                )
                return best_prompt.subject, best_prompt.topic

            # If no matches found, return default values
            logger.warning(
                "No matching prompts found",
                extra={"action": "select_prompt", "reason": "no_matches"},
            )
            return "physics", "generic"  # Return default values

        except Exception as e:
            logger.error(
                "Error selecting prompt",
                extra={"action": "select_prompt", "error": str(e)},
            )
            return "physics", "generic"  # Return default values on error

    def get_prompt_content(
        self, subject: str, topic: str, user_topic: str | None = None
    ) -> str:
        """Get the content of a prompt for the given subject and topic."""
        try:
            # Find the prompt in the database
            prompt = (
                self.db.query(Prompt)
                .filter(Prompt.subject == subject, Prompt.topic == topic)
                .first()
            )

            if not prompt:
                logger.warning(
                    "Prompt not found",
                    extra={
                        "action": "get_prompt_content",
                        "subject": subject,
                        "topic": topic,
                        "reason": "not_found",
                    },
                )
                return self.prompt_generator.generate_from_topic(
                    subject=subject,
                    topic=user_topic
                    or topic,  # Use user_topic if provided, otherwise use topic
                )

            # If user_topic is provided, use it to customize the prompt
            if user_topic and user_topic != topic:
                logger.info(
                    "Customizing prompt with user topic",
                    extra={
                        "action": "get_prompt_content",
                        "original_topic": topic,
                        "user_topic": user_topic,
                    },
                )
                return self.prompt_generator.generate_from_topic(
                    subject=subject, topic=user_topic
                )

            logger.info(
                "Using existing prompt",
                extra={
                    "action": "get_prompt_content",
                    "prompt_id": prompt.id,
                    "subject": subject,
                    "topic": topic,
                },
            )
            return str(prompt.content)  # Convert Column to string

        except Exception as e:
            logger.error(
                "Error getting prompt content",
                extra={
                    "action": "get_prompt_content",
                    "subject": subject,
                    "topic": topic,
                    "error": str(e),
                },
            )
            # Generate a new prompt as fallback
            return self.prompt_generator.generate_from_topic(
                subject=subject,
                topic=user_topic
                or topic,  # Use user_topic if provided, otherwise use topic
            )

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
        if hasattr(self, "db") and self.db is not None:
            self.db.close()

    def update_index(self):
        """Update the FAISS index with current prompts."""
        try:
            # Get all prompts from database
            self.prompts = self.db.query(Prompt).all()
            if not self.prompts:
                logger.warning(
                    "No prompts found in database",
                    extra={"action": "update_index", "reason": "no_prompts"},
                )
                return

            # Create FAISS index
            dimension = len(self.prompts[0].embedding)
            self.index = faiss.IndexFlatIP(
                dimension
            )  # Use inner product for cosine similarity

            # Add all embeddings to the index
            vectors = np.array([p.embedding for p in self.prompts])
            faiss.normalize_L2(vectors)  # Normalize vectors for cosine similarity
            self.index.add(n=vectors.shape[0], x=vectors)

            logger.info(
                "FAISS index updated",
                extra={
                    "action": "update_index",
                    "prompt_count": len(self.prompts),
                    "dimension": dimension,
                },
            )
        except Exception as e:
            logger.error(
                "Error updating FAISS index",
                extra={"action": "update_index", "error": str(e)},
            )
            raise

    def generate_embeddings_for_prompts(self) -> None:
        """Generate embeddings for all prompts that don't have them."""
        try:
            prompts_without_embeddings = [
                p for p in self.prompts if p.embedding is None
            ]
            if not prompts_without_embeddings:
                logger.info(
                    "No prompts need embeddings",
                    extra={"action": "generate_embeddings"},
                )
                return

            logger.info(
                "Generating embeddings for prompts",
                extra={
                    "action": "generate_embeddings",
                    "num_prompts": len(prompts_without_embeddings),
                },
            )

            for prompt in prompts_without_embeddings:
                # Generate embedding for the prompt
                embedding = self.model.encode(
                    prompt.content, convert_to_numpy=True, normalize_embeddings=True
                )
                prompt.embedding = embedding.tolist()
                prompt.updated_at = datetime.utcnow()

            # Save changes to database
            self.db.commit()
            logger.info(
                "Generated embeddings for prompts",
                extra={
                    "action": "generate_embeddings",
                    "num_prompts": len(prompts_without_embeddings),
                },
            )

            # Reinitialize the index with the new embeddings
            self.initialize_index()
        except Exception as e:
            logger.error(
                "Failed to generate embeddings",
                extra={"action": "generate_embeddings", "error": str(e)},
            )
            raise
