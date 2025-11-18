"""FastAPI application for semantic search of Warhammer 40K lore."""

import os
from typing import List
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

app = FastAPI(
    title="Warhammer 40K Search API",
    description="Semantic search engine for Warhammer 40K lore and content",
    version="1.0.0",
)

# Configuration from environment variables with defaults
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "warhammer40kLore")
MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")

# Initialize clients
try:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    model = SentenceTransformer(MODEL_NAME)
except Exception as e:
    raise RuntimeError(f"Failed to initialize API components: {e}") from e


class SearchResponse(BaseModel):
    """Response model for search results."""

    text: str
    score: float


@app.get("/search", response_model=List[SearchResponse])
def search(
    q: str = Query(..., min_length=1, description="Your question or query"),
    limit: int = Query(5, ge=1, le=100, description="Number of results to return"),
) -> List[SearchResponse]:
    """
    Perform semantic search on Warhammer 40K lore.

    Args:
        q: Search query string
        limit: Maximum number of results to return (1-100)

    Returns:
        List of search results with text and similarity scores

    Raises:
        HTTPException: If the search fails
    """
    try:
        # Encode the query
        query_vector = model.encode(q).tolist()

        # Search in Qdrant
        hits = client.search(
            collection_name=COLLECTION_NAME, query_vector=query_vector, limit=limit
        )

        return [
            SearchResponse(text=hit.payload["text"], score=hit.score) for hit in hits
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    try:
        # Verify Qdrant connection
        client.get_collections()
        return {
            "status": "healthy",
            "qdrant_host": QDRANT_HOST,
            "qdrant_port": QDRANT_PORT,
            "collection": COLLECTION_NAME,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
