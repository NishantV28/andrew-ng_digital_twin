import os
from typing import Dict, Iterable, List

CORPUS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "corpus")


def iter_corpus_files() -> Iterable[str]:
    if not os.path.exists(CORPUS_DIR):
        return []

    for root, _, files in os.walk(CORPUS_DIR):
        for filename in sorted(files):
            if filename.endswith(".txt"):
                yield os.path.join(root, filename)


def parse_document(filepath: str) -> Dict[str, str]:
    with open(filepath, "r", encoding="utf-8") as handle:
        content = handle.read()

    rel_path = os.path.relpath(filepath, CORPUS_DIR).replace("\\", "/")
    bucket = "style" if rel_path.startswith("style/") else "knowledge"

    metadata = {
        "title": os.path.basename(filepath),
        "source": os.path.basename(filepath),
        "author": "",
        "url": "",
        "date": "",
        "bucket": bucket,
    }

    for line in content.splitlines()[:8]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key in metadata and value:
            metadata[key] = value

    return {
        "filepath": filepath,
        "relative_path": rel_path,
        "content": content,
        **metadata,
    }


def list_corpus_documents() -> List[Dict[str, str]]:
    docs = []
    for filepath in iter_corpus_files():
        doc = parse_document(filepath)
        docs.append(
            {
                "filename": os.path.basename(filepath),
                "relative_path": doc["relative_path"],
                "title": doc["title"],
                "source": doc["source"],
                "author": doc["author"],
                "url": doc["url"],
                "date": doc["date"],
                "bucket": doc["bucket"],
                "word_count": len(doc["content"].split()),
                "snippet": doc["content"][:300] + ("..." if len(doc["content"]) > 300 else ""),
            }
        )
    return docs
