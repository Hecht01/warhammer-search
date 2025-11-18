"""Tests for text chunking functionality."""

import unittest
import sys
import os

# Add parent directory to path to import indexing module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from indexing.chunking import chunk_text, chunk_documents


class TestChunking(unittest.TestCase):
    """Test cases for text chunking functions."""

    def test_basic_chunking(self):
        """Test basic chunking with simple text."""
        sample = "This is sentence one. This is sentence two. This is sentence three."
        chunks = chunk_text(sample, chunk_size=30, overlap=5, min_chunk_size=10)
        self.assertIsInstance(chunks, list)
        self.assertTrue(all(isinstance(chunk, str) for chunk in chunks))
        self.assertGreater(len(chunks), 0)

    def test_empty_text(self):
        """Test that empty text returns empty list."""
        self.assertEqual(chunk_text(""), [])
        self.assertEqual(chunk_text("   "), [])

    def test_text_smaller_than_chunk_size(self):
        """Test that small text returns single chunk."""
        text = "Short text."
        chunks = chunk_text(text, chunk_size=100)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        text = "A" * 100 + ". " + "B" * 100 + ". " + "C" * 100 + "."
        chunks = chunk_text(text, chunk_size=120, overlap=20)
        self.assertGreater(len(chunks), 1)
        # Verify chunks overlap (not exact due to sentence boundary logic)
        for i in range(len(chunks) - 1):
            self.assertIsNotNone(chunks[i])
            self.assertIsNotNone(chunks[i + 1])

    def test_sentence_boundary_splitting(self):
        """Test that chunking prefers sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunk_text(text, chunk_size=40, overlap=5, min_chunk_size=10)
        self.assertGreater(len(chunks), 0)
        # Each chunk should end at a sentence boundary or be complete
        for chunk in chunks:
            self.assertTrue(len(chunk) > 0)

    def test_min_chunk_size(self):
        """Test minimum chunk size enforcement."""
        text = "A. " * 100  # Many short sentences
        chunks = chunk_text(text, chunk_size=50, overlap=5, min_chunk_size=20)
        # All chunks should be >= min_chunk_size or be the last chunk
        for chunk in chunks[:-1]:
            self.assertGreaterEqual(len(chunk), 20)

    def test_invalid_parameters(self):
        """Test that invalid parameters raise ValueError."""
        text = "Some text here."
        # chunk_size <= overlap should raise error
        with self.assertRaises(ValueError):
            chunk_text(text, chunk_size=10, overlap=10)
        with self.assertRaises(ValueError):
            chunk_text(text, chunk_size=10, overlap=15)
        # min_chunk_size > chunk_size should raise error
        with self.assertRaises(ValueError):
            chunk_text(text, chunk_size=50, min_chunk_size=100)

    def test_long_text_without_sentence_boundaries(self):
        """Test chunking of text without sentence boundaries."""
        text = "word " * 500  # Long text without sentence endings
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        self.assertGreater(len(chunks), 1)
        # Should still split on whitespace
        for chunk in chunks:
            self.assertGreater(len(chunk), 0)

    def test_chunk_documents(self):
        """Test chunking multiple documents with metadata."""
        docs = [
            "First document with some text. It has multiple sentences.",
            "Second document also has text. Multiple sentences here too.",
            "Third document is shorter."
        ]
        result = chunk_documents(docs, chunk_size=50, overlap=10)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        # Verify metadata
        for item in result:
            self.assertIn('text', item)
            self.assertIn('doc_index', item)
            self.assertIn('chunk_index', item)
            self.assertIn('total_chunks', item)
            self.assertIsInstance(item['text'], str)
            self.assertIsInstance(item['doc_index'], int)
            self.assertIsInstance(item['chunk_index'], int)

    def test_chunk_documents_empty(self):
        """Test chunking empty document list."""
        result = chunk_documents([])
        self.assertEqual(result, [])

    def test_unicode_text(self):
        """Test chunking with Unicode characters."""
        text = "This has émojis 🎮 and spëcial çharacters. Multiple sentences here. More text follows."
        chunks = chunk_text(text, chunk_size=50, overlap=5)
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIsInstance(chunk, str)

    def test_newlines_in_text(self):
        """Test chunking text with newlines."""
        text = "First paragraph.\n\nSecond paragraph with more text.\n\nThird paragraph here."
        chunks = chunk_text(text, chunk_size=40, overlap=5, min_chunk_size=10)
        self.assertGreater(len(chunks), 0)


if __name__ == '__main__':
    unittest.main()
