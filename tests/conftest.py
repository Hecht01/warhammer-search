"""Pytest configuration for mocking heavy dependencies during test collection."""

import sys
from unittest.mock import MagicMock
import numpy as np


# Create a realistic mock for SentenceTransformer
class MockSentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass

    def encode(self, texts, show_progress_bar=True):
        """Return a realistic numpy array of embeddings."""
        if isinstance(texts, str):
            texts = [texts]
        # Filter empty strings like the real implementation
        texts = [t for t in texts if t.strip()]
        # Return 384-dimensional embeddings
        return np.random.rand(len(texts), 384)


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
