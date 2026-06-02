import os
import pickle
from typing import Any, Dict, List, Optional

import numpy as np
from google import genai

from backend.corpus import CORPUS_DIR, iter_corpus_files, parse_document

STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "vector_store.pkl")


def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set. Please set it in your environment or .env file.")
    return genai.Client(api_key=api_key)


def get_embedding(client, text: str) -> List[float]:
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
    )
    if hasattr(response, "embeddings") and response.embeddings:
        return response.embeddings[0].values
    if hasattr(response, "embedding") and response.embedding:
        return response.embedding.values
    raise ValueError("Embedding response did not include embedding values.")


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 180) -> List[str]:
    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += chunk_size - overlap
    return chunks


def build_index() -> bool:
    client = get_client()
    documents: List[Dict[str, Any]] = []

    if not os.path.exists(CORPUS_DIR):
        os.makedirs(CORPUS_DIR, exist_ok=True)
        return False

    for filepath in iter_corpus_files():
        doc = parse_document(filepath)
        chunks = chunk_text(doc["content"])
        for index, chunk in enumerate(chunks):
            embedding = get_embedding(client, chunk)
            documents.append(
                {
                    "text": chunk,
                    "embedding": embedding,
                    "source": doc["source"],
                    "title": doc["title"],
                    "author": doc["author"],
                    "url": doc["url"],
                    "date": doc["date"],
                    "bucket": doc["bucket"],
                    "filename": os.path.basename(filepath),
                    "relative_path": doc["relative_path"],
                    "chunk_id": f"{doc['relative_path']}::{index}",
                }
            )

    if not documents:
        return False

    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "wb") as handle:
        pickle.dump(documents, handle)
    return True


def load_index() -> List[Dict[str, Any]]:
    if not os.path.exists(STORE_PATH):
        build_index()

    with open(STORE_PATH, "rb") as handle:
        documents = pickle.load(handle)

    if not isinstance(documents, list):
        raise ValueError("Vector store is corrupted or in an unexpected format.")
    return documents


def search_corpus(query: str, top_k: int = 4, bucket: Optional[str] = "knowledge") -> List[Dict[str, Any]]:
    documents = load_index()
    filtered = [doc for doc in documents if bucket is None or doc.get("bucket") == bucket]
    if not filtered:
        return []

    client = get_client()
    query_vector = np.array(get_embedding(client, query))
    query_norm = np.linalg.norm(query_vector)
    if query_norm == 0:
        return []

    results = []
    for doc in filtered:
        doc_vector = np.array(doc["embedding"])
        doc_norm = np.linalg.norm(doc_vector)
        score = 0.0 if doc_norm == 0 else float(np.dot(query_vector, doc_vector) / (query_norm * doc_norm))
        results.append(
            {
                "text": doc["text"],
                "source": doc["source"],
                "title": doc["title"],
                "author": doc.get("author", ""),
                "url": doc.get("url", ""),
                "date": doc.get("date", ""),
                "bucket": doc.get("bucket", "knowledge"),
                "filename": doc["filename"],
                "relative_path": doc.get("relative_path", doc["filename"]),
                "score": score,
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]
