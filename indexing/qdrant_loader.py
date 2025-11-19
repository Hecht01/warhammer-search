"""Qdrant vector database utilities for storing and managing embeddings."""

from typing import List
import uuid
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams


def init_qdrant_collection(
    collection_name: str = "warhammer40kLore",
    vector_size: int = 384,
    host: str = "localhost",
    port: int = 6333,
) -> QdrantClient:
    """
    Initialize a Qdrant collection with the specified parameters.

    Args:
        collection_name: Name of the collection to create
        vector_size: Dimensionality of the vectors
        host: Qdrant server host
        port: Qdrant server port

    Returns:
        QdrantClient instance connected to the database

    Raises:
        Exception: If connection to Qdrant fails or collection creation fails
    """
    try:
        client = QdrantClient(host=host, port=port)
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        return client
    except Exception as e:
        raise Exception(f"Failed to initialize Qdrant collection: {e}") from e


def upload_to_qdrant(
    client: QdrantClient, collection_name: str, texts: List[str], embeddings: np.ndarray
) -> None:
    """
    Upload text chunks and their embeddings to Qdrant.

    Args:
        client: QdrantClient instance
        collection_name: Name of the collection to upload to
        texts: List of text chunks
        embeddings: NumPy array of embeddings matching the texts

    Raises:
        ValueError: If texts and embeddings lengths don't match
        Exception: If upload to Qdrant fails
    """
    if len(texts) != len(embeddings):
        raise ValueError(
            f"Mismatch between texts ({len(texts)}) and embeddings ({len(embeddings)})"
        )

    if not texts:
        raise ValueError("Cannot upload empty texts and embeddings")

    try:
        points = [
            PointStruct(
                id=uuid.uuid4().int & 0xFFFFFFFFFFFFFFFF,  # Ensure positive 64-bit int
                vector=vector.tolist() if isinstance(vector, np.ndarray) else vector,
                payload={"text": text},
            )
            for text, vector in zip(texts, embeddings)
        ]

        client.upsert(collection_name=collection_name, points=points)
    except Exception as e:
        raise Exception(f"Failed to upload to Qdrant: {e}") from e
