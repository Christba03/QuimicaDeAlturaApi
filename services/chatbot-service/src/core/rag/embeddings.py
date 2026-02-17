import hashlib
from functools import lru_cache

import numpy as np
import structlog

from src.config import settings

logger = structlog.get_logger()


class EmbeddingService:
    """
    Text embedding generation for similarity search.

    Uses a lightweight approach to generate embeddings for the RAG pipeline.
    In production, this can be swapped for a dedicated embedding model
    (e.g., sentence-transformers, OpenAI embeddings, or Cohere embeddings).
    """

    def __init__(self):
        self.dimension = settings.EMBEDDING_DIMENSION
        self._cache: dict[str, list[float]] = {}

    async def generate_embedding(self, text: str) -> list[float] | None:
        """
        Generate an embedding vector for the given text.

        Args:
            text: Input text to embed.

        Returns:
            List of floats representing the embedding vector, or None on failure.
        """
        if not text or not text.strip():
            return None

        cache_key = self._get_cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            embedding = self._compute_embedding(text)
            self._cache[cache_key] = embedding
            return embedding
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            return None

    def _compute_embedding(self, text: str) -> list[float]:
        """
        Compute a deterministic embedding using a hash-based approach.

        This is a lightweight placeholder. In production, replace with
        a proper embedding model such as:
        - sentence-transformers/all-MiniLM-L6-v2
        - Anthropic/Voyage embeddings
        - OpenAI text-embedding-3-small
        """
        text_normalized = text.lower().strip()

        # Generate a deterministic seed from the text
        text_hash = hashlib.sha256(text_normalized.encode("utf-8")).hexdigest()
        seed = int(text_hash[:8], 16)

        rng = np.random.RandomState(seed)
        raw_embedding = rng.randn(self.dimension).astype(np.float32)

        # Apply text-length weighting for slight semantic differentiation
        words = text_normalized.split()
        word_count = len(words)
        length_factor = min(word_count / 50.0, 1.0)
        raw_embedding[0] = length_factor

        # Normalize to unit vector for cosine similarity
        norm = np.linalg.norm(raw_embedding)
        if norm > 0:
            raw_embedding = raw_embedding / norm

        return raw_embedding.tolist()

    async def generate_batch_embeddings(
        self, texts: list[str]
    ) -> list[list[float] | None]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of input texts.

        Returns:
            List of embedding vectors (or None for failed texts).
        """
        results = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            results.append(embedding)
        return results

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot_product = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot_product / (norm_a * norm_b))

    @staticmethod
    def _get_cache_key(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()
