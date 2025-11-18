"""Text embedding utilities using Sentence Transformers."""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(
    chunks: Union[List[str], str], show_progress: bool = True
) -> np.ndarray:
    """
    Embed text chunks using the Sentence Transformer model.

    Args:
        chunks: Single text string or list of text strings to embed
        show_progress: Whether to show a progress bar during encoding

    Returns:
        NumPy array of embeddings with shape (n_chunks, embedding_dim)

    Raises:
        ValueError: If chunks is empty or contains only empty strings
    """
    if not chunks:
        raise ValueError("Cannot embed empty input")

    # Convert single string to list
    if isinstance(chunks, str):
        chunks = [chunks]

    # Filter out empty strings
    non_empty_chunks = [c for c in chunks if c.strip()]
    if not non_empty_chunks:
        raise ValueError("Cannot embed chunks with only empty strings")

    return model.encode(non_empty_chunks, show_progress_bar=show_progress)
