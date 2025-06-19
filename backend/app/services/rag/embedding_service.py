"""Embedding service for generating text embeddings."""

import threading

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Service for generating embeddings using a sentence transformer model."""

    _model = None
    _lock = threading.Lock()

    @classmethod
    def get_model(cls):
        with cls._lock:
            if cls._model is None:
                cls._model = SentenceTransformer("all-MiniLM-L6-v2")
            return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> np.ndarray:
        model = cls.get_model()
        embedding = model.encode(text)
        return (
            np.array(embedding) if not isinstance(embedding, np.ndarray) else embedding
        )
