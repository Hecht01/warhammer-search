import unittest


class MyTestCase(unittest.TestCase):
    def test_chunking():
        sample = "This is sentence one. This is sentence two. This is sentence three."
        chunks = chunk_text(sample, max_tokens=5)
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert len(chunks) > 0


if __name__ == '__main__':
    unittest.main()
