"""Initialize Qdrant database with lore data on startup."""

from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
from indexing.chunking import chunk_text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collection_exists_and_has_data(client: QdrantClient, collection_name: str) -> bool:
    """Check if collection exists and has data."""
    try:
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection_name not in collection_names:
            return False

        # Check if collection has points
        count = client.count(collection_name=collection_name).count
        return count > 0
    except Exception:
        return False


def init_lore_data(
    host: str = "localhost",
    port: int = 6333,
    collection_name: str = "warhammer40kLore",
) -> None:
    """
    Initialize Qdrant collection with lore data if it doesn't exist.

    Args:
        host: Qdrant host
        port: Qdrant port
        collection_name: Name of the collection
    """
    client = QdrantClient(host=host, port=port)

    # Check if collection already has data
    if collection_exists_and_has_data(client, collection_name):
        logger.info(f"Collection '{collection_name}' already has data. Skipping init.")
        return

    logger.info(
        f"Collection '{collection_name}' is empty or doesn't exist. Initializing..."
    )

    # Find raw data files
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    txt_files = list(data_dir.glob("*.txt"))

    if not txt_files:
        logger.warning(f"No .txt files found in {data_dir}")
        return

    logger.info(f"Found {len(txt_files)} lore files to process")

    # Initialize model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Recreate collection
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    # Process each file
    all_chunks = []
    all_embeddings = []

    for txt_file in txt_files:
        logger.info(f"Processing {txt_file.name}...")

        # Read and chunk text
        with open(txt_file, "r", encoding="utf-8") as f:
            text = f.read()

        if not text.strip():
            continue

        chunks = chunk_text(text, chunk_size=500, overlap=50)
        logger.info(f"  Created {len(chunks)} chunks")

        # Embed chunks
        embeddings = model.encode(chunks, show_progress_bar=False)
        logger.info(f"  Generated {len(embeddings)} embeddings")

        all_chunks.extend(chunks)
        all_embeddings.extend(embeddings)

    # Upload to Qdrant in batches
    logger.info(f"Uploading {len(all_chunks)} chunks to Qdrant...")
    batch_size = 100

    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i : i + batch_size]
        batch_embeddings = all_embeddings[i : i + batch_size]

        points = [
            {
                "id": i + j,
                "vector": emb.tolist() if hasattr(emb, "tolist") else emb,
                "payload": {"text": chunk},
            }
            for j, (chunk, emb) in enumerate(zip(batch_chunks, batch_embeddings))
        ]

        client.upsert(collection_name=collection_name, points=points)

    logger.info(
        f"Successfully initialized collection '{collection_name}' with "
        f"{len(all_chunks)} chunks"
    )


if __name__ == "__main__":
    init_lore_data()
