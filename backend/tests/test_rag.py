import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from backend.corpus import clean_transcript_text, list_corpus_documents
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

    def test_transcript_cleaning_removes_generic_openers(self):
        text = "Welcome back to the course. Hello everyone. Gradient descent is an algorithm for minimizing a cost function. It updates parameters step by step."
        cleaned = clean_transcript_text(text)
        self.assertNotIn("Welcome back", cleaned)
        self.assertNotIn("Hello everyone", cleaned)
        self.assertIn("Gradient descent is an algorithm", cleaned)


if __name__ == "__main__":
    unittest.main()
