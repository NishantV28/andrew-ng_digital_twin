import os
import re
from typing import Dict, Iterable, List

CORPUS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "corpus")
TRANSCRIPT_LEADING_PATTERNS = [
    r"^welcome (back )?(to|everyone|everybody)\b.*",
    r"^hello (everyone|everybody)\b.*",
    r"^hi (everyone|everybody)\b.*",
    r"^good (morning|afternoon|evening)\b.*",
    r"^thanks for joining\b.*",
    r"^so welcome back\b.*",
    r"^let'?s take a look together\b.*",
    r"^let'?s go see\b.*",
]
TRANSCRIPT_INLINE_PATTERNS = [
    r"\blet'?s take a look together\b\.?",
    r"\blet'?s go see\b\.?",
]


def iter_corpus_files() -> Iterable[str]:
    if not os.path.exists(CORPUS_DIR):
        return []

    for root, _, files in os.walk(CORPUS_DIR):
        for filename in sorted(files):
            if filename.endswith(".txt"):
                yield os.path.join(root, filename)


def _extract_content_body(text: str) -> str:
    marker = "Content:"
    if marker in text:
        return text.split(marker, 1)[1].strip()
    return text.strip()


def _split_sentences(text: str) -> List[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def clean_transcript_text(text: str) -> str:
    sentences = _split_sentences(text)
    cleaned: List[str] = []
    dropping_intro = True

    for sentence in sentences:
        lowered = sentence.lower().strip()
        if dropping_intro and any(re.match(pattern, lowered) for pattern in TRANSCRIPT_LEADING_PATTERNS):
            continue
        dropping_intro = False
        cleaned.append(sentence)

    result = " ".join(cleaned)
    for pattern in TRANSCRIPT_INLINE_PATTERNS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", result).strip()


def parse_document(filepath: str) -> Dict[str, str]:
    with open(filepath, "r", encoding="utf-8") as handle:
        raw_text = handle.read()

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

    for line in raw_text.splitlines()[:8]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key in metadata and value:
            metadata[key] = value

    content = _extract_content_body(raw_text)
    if metadata["source"].lower() == "youtube":
        content = clean_transcript_text(content)

    return {
        "filepath": filepath,
        "relative_path": rel_path,
        "content": content,
        "raw_text": raw_text,
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
