"""Pytest configuration for mocking heavy dependencies during test collection."""

import sys
from unittest.mock import MagicMock
import numpy as np


# Create a realistic mock for SentenceTransformer
class MockSentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass

    def encode(self, texts, show_progress_bar=True):
        """Return a realistic numpy array of embeddings (deterministic based on input)."""
        if isinstance(texts, str):
            texts = [texts]
        # Filter empty strings like the real implementation
        texts = [t for t in texts if t.strip()]
        # Return 384-dimensional embeddings, deterministic based on text content
        embeddings = []
        for text in texts:
            # Create embeddings based on word content for semantic similarity
            # Use bag-of-words style: each word contributes to the embedding
            words = text.lower().split()
            embedding = np.zeros(384)
            for word in words:
                # Each word affects specific dimensions based on its hash
                word_hash = hash(word) % 384
                seed = hash(word) % (2**32)
                rng = np.random.RandomState(seed)
                # Add word contribution to embedding
                contribution = rng.rand(384) * 0.5
                embedding += contribution
            # Normalize so texts with different lengths are comparable
            if len(words) > 0:
                embedding = embedding / len(words)
            # Add small random component for uniqueness
            text_seed = hash(text) % (2**32)
            rng = np.random.RandomState(text_seed)
            embedding += rng.rand(384) * 0.1
            # Normalize to unit length (like real embeddings)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            embeddings.append(embedding)
        return np.array(embeddings)


# Create a realistic mock for PointStruct
class MockPointStruct:
    def __init__(self, id, vector, payload):
        self.id = id
        self.vector = vector
        self.payload = payload


# Create mock modules with the custom classes
class MockSentenceTransformersModule:
    SentenceTransformer = MockSentenceTransformer


class MockQdrantModels:
    PointStruct = MockPointStruct
    Distance = MagicMock()
    VectorParams = MagicMock()


class MockQdrantClient:
    QdrantClient = MagicMock
    models = MockQdrantModels()


# Mock heavy ML libraries before any tests try to import them
sys.modules["sentence_transformers"] = MockSentenceTransformersModule()
sys.modules["qdrant_client"] = MockQdrantClient()
sys.modules["qdrant_client.models"] = MockQdrantModels()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
