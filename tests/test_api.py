"""Tests for the FastAPI search endpoint."""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient  # noqa: E402


class TestSearchAPI(unittest.TestCase):
    """Test cases for the search API endpoint."""

    def setUp(self):
        """Set up test client and mocks before each test."""
        # Mock the Qdrant client and model before importing the app
        self.mock_qdrant_client = Mock()
        self.mock_model = Mock()

        # Patch the imports
        self.qdrant_patcher = patch('api.search.QdrantClient', return_value=self.mock_qdrant_client)
        self.model_patcher = patch('api.search.SentenceTransformer', return_value=self.mock_model)

        self.qdrant_patcher.start()
        self.model_patcher.start()

        # Import the app after patching
        from api.search import app
        self.client = TestClient(app)

    def tearDown(self):
        """Clean up patches after each test."""
        self.qdrant_patcher.stop()
        self.model_patcher.stop()

    def test_health_endpoint_healthy(self):
        """Test health check endpoint when Qdrant is available."""
        self.mock_qdrant_client.get_collections.return_value = Mock()

        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("qdrant_host", data)
        self.assertIn("collection", data)

    def test_health_endpoint_unhealthy(self):
        """Test health check endpoint when Qdrant is unavailable."""
        self.mock_qdrant_client.get_collections.side_effect = Exception("Connection failed")

        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertIn("error", data)

    def test_search_endpoint_success(self):
        """Test successful search query."""
        # Mock the model.encode to return a fake vector
        self.mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)

        # Mock Qdrant search results
        mock_hit1 = Mock()
        mock_hit1.payload = {"text": "The Emperor protects the Imperium."}
        mock_hit1.score = 0.95

        mock_hit2 = Mock()
        mock_hit2.payload = {"text": "Space Marines are elite warriors."}
        mock_hit2.score = 0.87

        self.mock_qdrant_client.search.return_value = [mock_hit1, mock_hit2]

        response = self.client.get("/search?q=Emperor")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["text"], "The Emperor protects the Imperium.")
        self.assertEqual(data[0]["score"], 0.95)
        self.assertEqual(data[1]["score"], 0.87)

    def test_search_endpoint_with_limit(self):
        """Test search with custom limit parameter."""
        self.mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)

        # Create 10 mock results
        mock_hits = []
        for i in range(10):
            hit = Mock()
            hit.payload = {"text": f"Result {i}"}
            hit.score = 0.9 - (i * 0.05)
            mock_hits.append(hit)

        self.mock_qdrant_client.search.return_value = mock_hits

        response = self.client.get("/search?q=test&limit=3")

        self.assertEqual(response.status_code, 200)
        # The API should request 3 results from Qdrant
        self.mock_qdrant_client.search.assert_called_once()
        call_args = self.mock_qdrant_client.search.call_args
        self.assertEqual(call_args.kwargs['limit'], 3)

    def test_search_endpoint_empty_query(self):
        """Test search with empty query string."""
        response = self.client.get("/search?q=")

        # Should return 422 validation error for empty string
        self.assertEqual(response.status_code, 422)

    def test_search_endpoint_missing_query(self):
        """Test search without query parameter."""
        response = self.client.get("/search")

        # Should return 422 validation error for missing required parameter
        self.assertEqual(response.status_code, 422)

    def test_search_endpoint_invalid_limit(self):
        """Test search with invalid limit values."""
        # Limit too small
        response = self.client.get("/search?q=test&limit=0")
        self.assertEqual(response.status_code, 422)

        # Limit too large
        response = self.client.get("/search?q=test&limit=101")
        self.assertEqual(response.status_code, 422)

        # Negative limit
        response = self.client.get("/search?q=test&limit=-5")
        self.assertEqual(response.status_code, 422)

    def test_search_endpoint_valid_limit_range(self):
        """Test search with valid limit values at boundaries."""
        self.mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)
        self.mock_qdrant_client.search.return_value = []

        # Minimum valid limit
        response = self.client.get("/search?q=test&limit=1")
        self.assertEqual(response.status_code, 200)

        # Maximum valid limit
        response = self.client.get("/search?q=test&limit=100")
        self.assertEqual(response.status_code, 200)

    def test_search_endpoint_qdrant_failure(self):
        """Test search when Qdrant search fails."""
        self.mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)
        self.mock_qdrant_client.search.side_effect = Exception("Qdrant connection error")

        response = self.client.get("/search?q=test")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Search failed", data["detail"])

    def test_search_endpoint_encoding_failure(self):
        """Test search when text encoding fails."""
        self.mock_model.encode.side_effect = Exception("Encoding error")

        response = self.client.get("/search?q=test")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)

    def test_search_endpoint_no_results(self):
        """Test search when no results are found."""
        self.mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)
        self.mock_qdrant_client.search.return_value = []

        response = self.client.get("/search?q=nonexistent")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 0)

    def test_search_endpoint_unicode_query(self):
        """Test search with Unicode characters in query."""
        self.mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)

        mock_hit = Mock()
        mock_hit.payload = {"text": "Craftworld Iyandèn"}
        mock_hit.score = 0.9
        self.mock_qdrant_client.search.return_value = [mock_hit]

        response = self.client.get("/search?q=Iyandèn")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)

    def test_search_endpoint_long_query(self):
        """Test search with very long query."""
        self.mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)
        self.mock_qdrant_client.search.return_value = []

        long_query = " ".join(["word"] * 1000)
        response = self.client.get(f"/search?q={long_query}")

        self.assertEqual(response.status_code, 200)

    def test_search_endpoint_special_characters(self):
        """Test search with special characters."""
        self.mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)

        mock_hit = Mock()
        mock_hit.payload = {"text": "WAAAGH!!!"}
        mock_hit.score = 0.85
        self.mock_qdrant_client.search.return_value = [mock_hit]

        response = self.client.get("/search?q=WAAAGH!!!")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)

    def test_search_response_structure(self):
        """Test that search response has correct structure."""
        self.mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)

        mock_hit = Mock()
        mock_hit.payload = {"text": "Test content"}
        mock_hit.score = 0.9
        self.mock_qdrant_client.search.return_value = [mock_hit]

        response = self.client.get("/search?q=test")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        # Check first result structure
        result = data[0]
        self.assertIn("text", result)
        self.assertIn("score", result)
        self.assertIsInstance(result["text"], str)
        self.assertIsInstance(result["score"], (int, float))

    def test_openapi_schema(self):
        """Test that OpenAPI schema is available."""
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)

        schema = response.json()
        self.assertIn("info", schema)
        self.assertIn("paths", schema)
        self.assertIn("/search", schema["paths"])
        self.assertIn("/health", schema["paths"])


class TestAPIIntegration(unittest.TestCase):
    """Integration tests for the API (require actual model loading)."""

    @unittest.skip("Integration test - requires model download")
    def test_actual_search(self):
        """Test actual search with real model (skipped by default)."""
        # This test would require actual Qdrant and model
        # Useful for manual integration testing
        pass


if __name__ == '__main__':
    unittest.main()
