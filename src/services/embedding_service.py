"""Embedding service for generating and managing embeddings."""

import logging
import os
from typing import List, Optional

import numpy as np
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using OpenAI API.

    Uses text-embedding-3-small model for 1536-dimensional embeddings.
    """

    # OpenAI embedding model
    MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSION = 1536

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize embedding service.

        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        """
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = self.MODEL

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            1536-dimensional embedding vector

        Raises:
            ValueError: If embedding fails
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
            )

            if response.data:
                return response.data[0].embedding

            raise ValueError("No embedding returned from OpenAI API")

        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise

    async def embed_texts(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Batches requests for efficiency.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call (max 2048)

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If any embedding fails
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.info(f"Generating embeddings for batch {i // batch_size + 1} ({len(batch)} texts)")

            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )

                # Sort by index to maintain order
                sorted_data = sorted(response.data, key=lambda x: x.index)
                batch_embeddings = [item.embedding for item in sorted_data]

                embeddings.extend(batch_embeddings)

            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch: {str(e)}")
                raise

        logger.info(f"Generated {len(embeddings)} embeddings total")
        return embeddings

    async def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """
        Generate embeddings for document chunks.

        Args:
            chunks: List of text chunks

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If embedding fails
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        return await self.embed_texts(chunks)

    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate embedding dimensions.

        Args:
            embedding: Embedding vector

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(embedding, (list, np.ndarray)):
            return False

        if len(embedding) != self.EMBEDDING_DIMENSION:
            logger.warning(
                f"Invalid embedding dimension: {len(embedding)} != {self.EMBEDDING_DIMENSION}"
            )
            return False

        return True

    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        embedding1 = np.array(embedding1)
        embedding2 = np.array(embedding2)

        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def batch_cosine_similarity(
        self,
        query_embedding: List[float],
        embeddings: List[List[float]],
    ) -> List[float]:
        """
        Calculate cosine similarity between query and multiple embeddings.

        Args:
            query_embedding: Query embedding vector
            embeddings: List of embedding vectors

        Returns:
            List of similarity scores
        """
        query = np.array(query_embedding)

        similarities = []
        for embedding in embeddings:
            embedding = np.array(embedding)
            dot_product = np.dot(query, embedding)
            norm_query = np.linalg.norm(query)
            norm_embedding = np.linalg.norm(embedding)

            if norm_query == 0 or norm_embedding == 0:
                similarities.append(0.0)
            else:
                similarity = float(dot_product / (norm_query * norm_embedding))
                similarities.append(similarity)

        return similarities
