import unittest
import numpy as np

from indexing.embed import embed_texts

class MyTestCase(unittest.TestCase):

    def test_embed_texts_shape(self):
        texts = ["The Emperor protects.", "Horus was the Warmaster."]
        embeddings = embed_texts(texts)

        assert isinstance(embeddings, np.ndarray), "Embeddings should be a numpy array"
        assert embeddings.shape[0] == len(texts), "Number of embeddings should match number of inputs"
        assert embeddings.shape[1] > 0, "Embeddings should have non-zero dimension"

    def test_embed_texts_determinism(self):
        texts = ["Cadia stood."]
        emb1 = embed_texts(texts)
        emb2 = embed_texts(texts)

        assert np.allclose(emb1, emb2), "Embedding should be deterministic for same input"

    def test_embed_texts_with_empty_input(self):
        texts = [""]
        embeddings = embed_texts(texts)

        assert embeddings.shape[0] == 1, "Should return one embedding for one input"
        assert embeddings.shape[1] > 0, "Embedding should have dimensions even if text is empty"


if __name__ == '__main__':
    unittest.main()
