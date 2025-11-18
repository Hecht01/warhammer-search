"""Tests for Qdrant database operations."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from indexing.qdrant_loader import init_qdrant_collection, upload_to_qdrant


class TestQdrantLoader(unittest.TestCase):
    """Test cases for Qdrant database operations."""

    @patch('indexing.qdrant_loader.QdrantClient')
    def test_init_qdrant_collection_success(self, mock_client_class):
        """Test successful Qdrant collection initialization."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        result = init_qdrant_collection(
            collection_name="test_collection",
            vector_size=384,
            host="localhost",
            port=6333
        )

        # Verify client was created with correct parameters
        mock_client_class.assert_called_once_with(host="localhost", port=6333)

        # Verify collection was recreated
        mock_client.recreate_collection.assert_called_once()
        call_args = mock_client.recreate_collection.call_args
        self.assertEqual(call_args.kwargs['collection_name'], "test_collection")

        # Verify client is returned
        self.assertEqual(result, mock_client)

    @patch('indexing.qdrant_loader.QdrantClient')
    def test_init_qdrant_collection_default_params(self, mock_client_class):
        """Test collection initialization with default parameters."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        result = init_qdrant_collection()

        # Verify defaults
        call_args = mock_client.recreate_collection.call_args
        self.assertEqual(call_args.kwargs['collection_name'], "warhammer40kLore")

    @patch('indexing.qdrant_loader.QdrantClient')
    def test_init_qdrant_collection_connection_failure(self, mock_client_class):
        """Test collection initialization when connection fails."""
        mock_client_class.side_effect = Exception("Connection refused")

        with self.assertRaises(Exception) as context:
            init_qdrant_collection()

        self.assertIn("Failed to initialize Qdrant collection", str(context.exception))

    @patch('indexing.qdrant_loader.QdrantClient')
    def test_init_qdrant_collection_creation_failure(self, mock_client_class):
        """Test collection initialization when collection creation fails."""
        mock_client = Mock()
        mock_client.recreate_collection.side_effect = Exception("Creation failed")
        mock_client_class.return_value = mock_client

        with self.assertRaises(Exception) as context:
            init_qdrant_collection()

        self.assertIn("Failed to initialize Qdrant collection", str(context.exception))

    def test_upload_to_qdrant_success(self):
        """Test successful upload of texts and embeddings."""
        mock_client = Mock()
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = np.array([[0.1] * 384, [0.2] * 384, [0.3] * 384])

        upload_to_qdrant(mock_client, "test_collection", texts, embeddings)

        # Verify upsert was called
        mock_client.upsert.assert_called_once()
        call_args = mock_client.upsert.call_args

        # Verify collection name
        self.assertEqual(call_args.kwargs['collection_name'], "test_collection")

        # Verify points
        points = call_args.kwargs['points']
        self.assertEqual(len(points), 3)

        # Verify each point has correct structure
        for i, point in enumerate(points):
            self.assertIsNotNone(point.id)
            self.assertEqual(point.payload["text"], texts[i])
            # Vector should be a list
            self.assertIsInstance(point.vector, list)
            self.assertEqual(len(point.vector), 384)

    def test_upload_to_qdrant_empty_data(self):
        """Test upload with empty data raises error."""
        mock_client = Mock()

        with self.assertRaises(ValueError) as context:
            upload_to_qdrant(mock_client, "test_collection", [], np.array([]))

        self.assertIn("Cannot upload empty", str(context.exception))

    def test_upload_to_qdrant_mismatched_lengths(self):
        """Test upload with mismatched text and embedding counts."""
        mock_client = Mock()
        texts = ["Text 1", "Text 2"]
        embeddings = np.array([[0.1] * 384])  # Only one embedding

        with self.assertRaises(ValueError) as context:
            upload_to_qdrant(mock_client, "test_collection", texts, embeddings)

        self.assertIn("Mismatch between texts", str(context.exception))

    def test_upload_to_qdrant_single_item(self):
        """Test upload of a single text and embedding."""
        mock_client = Mock()
        texts = ["Single text"]
        embeddings = np.array([[0.1] * 384])

        upload_to_qdrant(mock_client, "test_collection", texts, embeddings)

        mock_client.upsert.assert_called_once()
        points = mock_client.upsert.call_args.kwargs['points']
        self.assertEqual(len(points), 1)

    def test_upload_to_qdrant_large_batch(self):
        """Test upload of large batch of data."""
        mock_client = Mock()
        num_items = 1000
        texts = [f"Text {i}" for i in range(num_items)]
        embeddings = np.random.rand(num_items, 384)

        upload_to_qdrant(mock_client, "test_collection", texts, embeddings)

        mock_client.upsert.assert_called_once()
        points = mock_client.upsert.call_args.kwargs['points']
        self.assertEqual(len(points), num_items)

    def test_upload_to_qdrant_handles_list_vectors(self):
        """Test upload handles both numpy arrays and lists as vectors."""
        mock_client = Mock()
        texts = ["Text 1"]
        # Use a list instead of numpy array
        embeddings = [[0.1] * 384]

        upload_to_qdrant(mock_client, "test_collection", texts, embeddings)

        mock_client.upsert.assert_called_once()

    def test_upload_to_qdrant_upload_failure(self):
        """Test upload when Qdrant upsert fails."""
        mock_client = Mock()
        mock_client.upsert.side_effect = Exception("Upload failed")

        texts = ["Text 1"]
        embeddings = np.array([[0.1] * 384])

        with self.assertRaises(Exception) as context:
            upload_to_qdrant(mock_client, "test_collection", texts, embeddings)

        self.assertIn("Failed to upload to Qdrant", str(context.exception))

    def test_upload_to_qdrant_unicode_text(self):
        """Test upload with Unicode characters in text."""
        mock_client = Mock()
        texts = ["Craftworld Iyandèn 🏛️", "T'au Empire"]
        embeddings = np.array([[0.1] * 384, [0.2] * 384])

        upload_to_qdrant(mock_client, "test_collection", texts, embeddings)

        mock_client.upsert.assert_called_once()
        points = mock_client.upsert.call_args.kwargs['points']
        self.assertEqual(points[0].payload["text"], "Craftworld Iyandèn 🏛️")
        self.assertEqual(points[1].payload["text"], "T'au Empire")

    def test_upload_to_qdrant_unique_ids(self):
        """Test that uploaded points have unique IDs."""
        mock_client = Mock()
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = np.array([[0.1] * 384, [0.2] * 384, [0.3] * 384])

        upload_to_qdrant(mock_client, "test_collection", texts, embeddings)

        points = mock_client.upsert.call_args.kwargs['points']
        ids = [point.id for point in points]

        # All IDs should be unique
        self.assertEqual(len(ids), len(set(ids)))

        # All IDs should be valid integers
        for point_id in ids:
            self.assertIsInstance(point_id, int)
            self.assertGreaterEqual(point_id, 0)


class TestQdrantIntegration(unittest.TestCase):
    """Integration tests for Qdrant operations."""

    @unittest.skip("Integration test - requires running Qdrant instance")
    def test_full_workflow(self):
        """Test full workflow of init and upload (skipped by default)."""
        # This would test against a real Qdrant instance
        # Useful for manual integration testing
        pass


if __name__ == '__main__':
    unittest.main()
