"""Text chunking utilities for splitting documents into semantic chunks."""

from typing import List
import re


def chunk_text(
    text: str, chunk_size: int = 500, overlap: int = 50, min_chunk_size: int = 50
) -> List[str]:
    """
    Split text into overlapping chunks, preferring sentence boundaries.

    Args:
        text: The text to chunk
        chunk_size: Target size for each chunk in characters
        overlap: Number of characters to overlap between chunks
        min_chunk_size: Minimum size for a chunk (smaller chunks are merged)

    Returns:
        List of text chunks

    Raises:
        ValueError: If chunk_size <= overlap or min_chunk_size > chunk_size
    """
    if not text or not text.strip():
        return []

    if chunk_size <= overlap:
        raise ValueError(
            f"chunk_size ({chunk_size}) must be greater than overlap ({overlap})"
        )

    if min_chunk_size > chunk_size:
        raise ValueError(
            f"min_chunk_size ({min_chunk_size}) must be <= chunk_size ({chunk_size})"
        )

    # Clean up the text
    text = text.strip()

    # If text is smaller than chunk_size, return it as-is
    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    last_start = -1  # Track last start position to ensure progress

    while start < len(text):
        # Determine end position for this chunk
        end = start + chunk_size

        # If this is the last chunk, take everything remaining
        if end >= len(text):
            chunk = text[start:].strip()
            if chunk and len(chunk) >= min_chunk_size:
                chunks.append(chunk)
            elif chunk and chunks:
                # Merge small final chunk with previous chunk
                chunks[-1] = chunks[-1] + " " + chunk
            elif chunk:
                # Only chunk and it's small, but keep it anyway
                chunks.append(chunk)
            break

        # Try to find a sentence boundary near the end
        chunk_text = text[start:end]

        # Look for sentence endings: . ! ? followed by space or newline
        sentence_endings = list(re.finditer(r"[.!?][\s\n]", chunk_text))

        if sentence_endings:
            # Use the last sentence ending in the chunk
            last_ending = sentence_endings[-1]
            actual_end = start + last_ending.end()
        else:
            # No sentence boundary found, try to break on whitespace
            remaining_text = text[start:end]
            last_space = remaining_text.rfind(" ")

            if (
                last_space > chunk_size // 2
            ):  # Only break on space if it's not too early
                actual_end = start + last_space + 1
            else:
                actual_end = end

        chunk = text[start:actual_end].strip()

        if chunk and len(chunk) >= min_chunk_size:
            chunks.append(chunk)
        elif chunk and chunks:
            # Merge with previous chunk if too small
            chunks[-1] = chunks[-1] + " " + chunk

        # Move start position, accounting for overlap
        start = actual_end - overlap

        # Ensure we make progress (avoid infinite loop)
        if start <= last_start:
            start = actual_end

        last_start = start

    return chunks


def chunk_documents(
    documents: List[str],
    chunk_size: int = 500,
    overlap: int = 50,
    min_chunk_size: int = 50,
) -> List[dict]:
    """
    Chunk multiple documents and track source document index.

    Args:
        documents: List of documents to chunk
        chunk_size: Target size for each chunk in characters
        overlap: Number of characters to overlap between chunks
        min_chunk_size: Minimum size for a chunk

    Returns:
        List of dicts with 'text', 'doc_index', and 'chunk_index' keys
    """
    if not documents:
        return []

    result = []

    for doc_idx, doc in enumerate(documents):
        chunks = chunk_text(doc, chunk_size, overlap, min_chunk_size)

        for chunk_idx, chunk in enumerate(chunks):
            result.append(
                {
                    "text": chunk,
                    "doc_index": doc_idx,
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks),
                }
            )

    return result
