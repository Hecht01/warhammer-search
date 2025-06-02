from fastapi import FastAPI, Query
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import SearchRequest, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

app = FastAPI()
client = QdrantClient(host="localhost", port=6333)
model = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME = "warhammer"

class SearchResponse(BaseModel):
    text: str
    score: float


@app.get("/search", response_model=list[SearchResponse])
def search(q: str = Query(..., description="Your question or query")):
    query_vector = model.encode(q).tolist()
    hits = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=5
    )

    return [{"text": hit.payload["text"], "score": hit.score} for hit in hits]
