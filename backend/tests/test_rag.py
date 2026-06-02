import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from backend.corpus import list_corpus_documents
from backend.rag import chunk_text


class TestRAGPipeline(unittest.TestCase):
    def test_chunking(self):
        text = "This is a long piece of text that we want to chunk. " * 40
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        self.assertGreater(len(chunks), 1)
        self.assertLessEqual(len(chunks[0]), 100)

    def test_corpus_listing_exposes_buckets(self):
        docs = list_corpus_documents()
        self.assertTrue(any(doc["bucket"] == "knowledge" for doc in docs))


if __name__ == "__main__":
    unittest.main()
