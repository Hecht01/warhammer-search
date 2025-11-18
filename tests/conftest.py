"""Pytest configuration for mocking heavy dependencies during test collection."""

import sys
from unittest.mock import MagicMock

# Mock heavy ML libraries before any tests try to import them
# This allows tests to run without installing PyTorch, sentence-transformers, etc.

mock_modules = [
    "sentence_transformers",
    "qdrant_client",
    "qdrant_client.models",
    "torch",
    "transformers",
]

for module_name in mock_modules:
    sys.modules[module_name] = MagicMock()
