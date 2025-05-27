from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
import uuid


def init_qdrant_collection(collection_name="warhammer40kLore", vector_size=384):
    client = QdrantClient(":localhost:")  # or use localhost if Qdrant runs locally
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
    return client


def upload_to_qdrant(client, collection_name, texts, embeddings):
    points = [
        PointStruct(id=uuid.uuid4().int >> 64, vector=vector, payload={"text": text})
        for text, vector in zip(texts, embeddings)
    ]

    client.upsert(collection_name=collection_name, points=points)
