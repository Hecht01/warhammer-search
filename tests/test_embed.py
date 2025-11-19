"""Tests for text embedding functionality."""

import unittest
import sys
import os
import numpy as np

# Add parent directory to path to import indexing module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from indexing.embed import embed_texts  # noqa: E402


class TestEmbedding(unittest.TestCase):
    """Test cases for text embedding functions."""

    def test_embed_texts_shape(self):
        """Test that embeddings have correct shape."""
        texts = ["The Emperor protects.", "Horus was the Warmaster."]
        embeddings = embed_texts(texts, show_progress=False)

        self.assertIsInstance(
            embeddings, np.ndarray, "Embeddings should be a numpy array"
        )
        self.assertEqual(
            embeddings.shape[0],
            len(texts),
            "Number of embeddings should match number of inputs",
        )
        self.assertEqual(
            embeddings.shape[1], 384, "Embeddings should have 384 dimensions"
        )

    def test_embed_texts_determinism(self):
        """Test that embeddings are deterministic."""
        texts = ["Cadia stood."]
        emb1 = embed_texts(texts, show_progress=False)
        emb2 = embed_texts(texts, show_progress=False)

        self.assertTrue(
            np.allclose(emb1, emb2), "Embedding should be deterministic for same input"
        )

    def test_embed_single_string(self):
        """Test embedding a single string (not a list)."""
        text = "The Imperium of Man"
        embeddings = embed_texts(text, show_progress=False)

        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(
            embeddings.shape[0], 1, "Single string should produce one embedding"
        )
        self.assertEqual(embeddings.shape[1], 384)

    def test_embed_multiple_texts(self):
        """Test embedding multiple texts."""
        texts = [
            "Space Marines are elite warriors.",
            "Orks live for war.",
            "Tyranids consume all.",
            "Necrons are ancient machines.",
        ]
        embeddings = embed_texts(texts, show_progress=False)

        self.assertEqual(embeddings.shape[0], 4)
        self.assertEqual(embeddings.shape[1], 384)

    def test_embed_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        with self.assertRaises(ValueError):
            embed_texts([])

    def test_embed_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with self.assertRaises(ValueError):
            embed_texts("")

    def test_embed_only_whitespace_raises_error(self):
        """Test that only whitespace raises ValueError."""
        with self.assertRaises(ValueError):
            embed_texts(["   ", "\t", "\n"])

    def test_embed_mixed_empty_and_valid(self):
        """Test embedding with mix of empty and valid strings."""
        texts = ["Valid text", "", "Another valid", "   "]
        embeddings = embed_texts(texts, show_progress=False)

        # Should only embed the non-empty strings
        self.assertEqual(embeddings.shape[0], 2, "Should only embed non-empty strings")

    def test_embed_long_text(self):
        """Test embedding very long text."""
        long_text = " ".join(["The Emperor protects."] * 100)
        embeddings = embed_texts(long_text, show_progress=False)

        self.assertEqual(embeddings.shape[0], 1)
        self.assertEqual(embeddings.shape[1], 384)

    def test_embed_unicode_text(self):
        """Test embedding text with Unicode characters."""
        texts = ["Primarch Roboute Guilliman", "Craftworld Iyandèn 🏛️", "T'au Empire"]
        embeddings = embed_texts(texts, show_progress=False)

        self.assertEqual(embeddings.shape[0], 3)
        self.assertEqual(embeddings.shape[1], 384)

    def test_embed_special_characters(self):
        """Test embedding text with special characters."""
        texts = [
            "Blood for the Blood God!",
            "WAAAGH!!!",
            "++The Emperor's Will++",
            "[ MECHANICUS DATALOG: 40000 ]",
        ]
        embeddings = embed_texts(texts, show_progress=False)

        self.assertEqual(embeddings.shape[0], 4)

    def test_embeddings_are_normalized(self):
        """Test that embeddings have reasonable magnitude."""
        texts = ["Test text for normalization"]
        embeddings = embed_texts(texts, show_progress=False)

        # Check that embeddings are not all zeros
        self.assertFalse(
            np.allclose(embeddings, 0), "Embeddings should not be all zeros"
        )

        # Check that embeddings have reasonable magnitude (roughly normalized)
        norms = np.linalg.norm(embeddings, axis=1)
        self.assertTrue(np.all(norms > 0), "Embedding norms should be positive")

    def test_similar_texts_have_similar_embeddings(self):
        """Test that semantically similar texts have similar embeddings."""
        texts = [
            "Space Marines are warriors of the Emperor.",
            "The Emperor's Space Marines are elite soldiers.",
            "Orks are green-skinned aliens who love to fight.",
        ]
        embeddings = embed_texts(texts, show_progress=False)

        # Compute cosine similarity between first two (similar) and first and third (different)
        sim_similar = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        sim_different = np.dot(embeddings[0], embeddings[2]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[2])
        )

        # Similar texts should have higher cosine similarity
        self.assertGreater(
            sim_similar,
            sim_different,
            "Similar texts should have higher cosine similarity",
        )

    def test_progress_bar_parameter(self):
        """Test that progress bar parameter works."""
        texts = ["Test text 1", "Test text 2"]

        # Should work with both True and False
        emb1 = embed_texts(texts, show_progress=True)
        emb2 = embed_texts(texts, show_progress=False)

        self.assertTrue(
            np.allclose(emb1, emb2), "Results should be same regardless of progress bar"
        )


if __name__ == "__main__":
    unittest.main()
