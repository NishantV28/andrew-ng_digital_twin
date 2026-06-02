import json
import re
from typing import Any, Dict, List, Tuple

from google.genai import types

from backend.memory import (
    add_topic_discussed,
    get_chat_history,
    get_topics_discussed,
    get_user_facts,
    update_user_fact,
)
from backend.rag import get_client, search_corpus

ANDREW_NG_PERSONA = """You are a digital twin of Andrew Ng.
Your job is to answer with Andrew Ng's warmth, structure, and teaching style while staying honest about uncertainty.

Rules:
- For every answer, start with a short direct definition or direct answer in 1 to 2 sentences.
- Then add a short explanation grounded in the retrieved knowledge context.
- Lead with intuition, then structure, then practical advice.
- Prefer concise paragraphs or short numbered lists for explanations.
- Sound encouraging, calm, and teacher-like.
- Stay grounded in provided source material for factual claims.
- Use the retrieved knowledge context only for factual claims, and rewrite transcript language into clean written prose.
- Do not copy greetings, filler, or lecture-opening phrasing from transcripts.
- Keep citations at the end of the sentence in square brackets, such as [Autonomous Helicopter].
- Treat short social posts and style examples as tone guidance, not as primary factual evidence.
- Never claim to be the real Andrew Ng. When needed, phrase things as "in Andrew Ng's style" or "based on Andrew Ng's work."
- Be timeline aware when discussing career phases, papers, courses, or shifts in focus.
- When giving ML project advice, lean toward data-centric AI, strong baselines, and error analysis.
- End on a complete sentence and stop once the explanation is complete.
"""


def build_system_prompt(session_id: str) -> str:
    facts = get_user_facts(session_id)
    topics = get_topics_discussed(session_id)

    sections = [ANDREW_NG_PERSONA]

    if facts:
        sections.append("What you remember about this user:")
        sections.extend(f"- {key}: {info['value']}" for key, info in facts.items())

    if topics:
        sections.append("Topics already discussed with this user:")
        sections.extend(f"- {topic}: {info['summary']}" for topic, info in topics.items())

    return "\n".join(sections)


def _format_grounding_context(rag_hits: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    citations: List[Dict[str, Any]] = []
    context_blocks: List[str] = []

    for hit in rag_hits:
        if hit["score"] < 0.20:
            continue
        citations.append(
            {
                "title": hit["title"],
                "source": hit["source"],
                "score": hit["score"],
                "snippet": hit["text"][:240] + ("..." if len(hit["text"]) > 240 else ""),
                "url": hit.get("url", ""),
                "bucket": hit.get("bucket", "knowledge"),
            }
        )
        context_blocks.append(
            "\n".join(
                [
                    f"TITLE: {hit['title']}",
                    f"SOURCE: {hit['source']}",
                    f"DATE: {hit.get('date', '')}",
                    f"URL: {hit.get('url', '')}",
                    hit["text"],
                ]
            )
        )

    if not context_blocks:
        return "", citations

    return "Grounding context:\n\n" + "\n\n---\n\n".join(context_blocks), citations


def _format_style_context(style_hits: List[Dict[str, Any]]) -> str:
    examples = [hit["text"][:200].strip() for hit in style_hits if hit["score"] >= 0.18]
    if not examples:
        return ""

    return "Style hints from Andrew-like material:\n- " + "\n- ".join(example.replace("\n", " ") for example in examples)


def _finalize_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    if text.endswith((".", "!", "?", "]")):
        return text

    sentence_endings = list(re.finditer(r"[.!?](?:\s*\[[^\]]+\])?(?=\s|$)", text))
    if sentence_endings:
        return text[: sentence_endings[-1].end()].strip()

    return text


def generate_andrew_response(session_id: str, user_query: str) -> Tuple[str, List[Dict[str, Any]]]:
    client = get_client()
    rag_hits = search_corpus(user_query, top_k=4, bucket="knowledge")
    style_hits = search_corpus(user_query, top_k=2, bucket="style")

    grounding_context, citations = _format_grounding_context(rag_hits)
    style_context = _format_style_context(style_hits)
    history = get_chat_history(session_id, limit=10)
    system_instruction = build_system_prompt(session_id)

    contents: List[types.Content] = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

    user_sections = [f"User question:\n{user_query}"]
    if grounding_context:
        user_sections.append(grounding_context)
    if style_context:
        user_sections.append(style_context)
    user_sections.append("Answer in Andrew Ng's teaching style, but make no claim that this is Andrew's actual voice.")
    user_sections.append(
        "Format the answer as:\nDefinition: <1 to 2 sentences>\nExplanation: <2 to 4 concise sentences>\n"
        "Use only the retrieved knowledge context for the factual content."
    )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text="\n\n".join(user_sections))],
        )
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.35,
            max_output_tokens=500,
        ),
    )
    return _finalize_response(response.text), citations


def run_memory_extractor(session_id: str, user_query: str, agent_response: str) -> None:
    client = get_client()
    extraction_prompt = f"""Extract durable user memory from this conversation turn.

Return strict JSON only.

Conversation:
User: {user_query}
Assistant: {agent_response}

Schema:
{{
  "user_facts": {{
    "user_name": "string",
    "background": "string",
    "learning_goals": "string",
    "project_context": "string"
  }},
  "topics_discussed": {{
    "topic": "summary"
  }}
}}

Rules:
- Only store facts that are explicit or strongly implied.
- Keep summaries compact.
- Use empty objects when nothing new was learned.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=extraction_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        raw_text = re.sub(r"^```json\s*", "", response.text.strip())
        raw_text = re.sub(r"\s*```$", "", raw_text)
        data = json.loads(raw_text)
    except Exception:
        return

    for key, value in data.get("user_facts", {}).items():
        if isinstance(value, str) and value.strip():
            update_user_fact(session_id, key.replace("_", " ").title(), value.strip())

    for topic, summary in data.get("topics_discussed", {}).items():
        if isinstance(topic, str) and isinstance(summary, str) and topic.strip() and summary.strip():
            add_topic_discussed(session_id, topic.strip(), summary.strip())
