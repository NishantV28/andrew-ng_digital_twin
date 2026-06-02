import json
import uuid
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from backend.agent import generate_andrew_response, run_memory_extractor
from backend.corpus import list_corpus_documents
from backend.memory import get_chat_history, get_memory_state, reset_session_memory, save_message
from backend.rag import STORE_PATH, build_index

load_dotenv()

st.set_page_config(page_title="Andrew Ng Digital Twin", page_icon="AI", layout="wide")
EVALUATION_PATH = Path(__file__).parent / "data" / "evaluation" / "evaluation_suite.json"


def ensure_session_id() -> str:
    params = st.query_params
    if "session_id" not in st.session_state:
        session_id = params.get("session_id", "")
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:10]}"
            st.query_params["session_id"] = session_id
        st.session_state.session_id = session_id
    return st.session_state.session_id


def render_speech(text: str) -> None:
    payload = json.dumps(text)
    components.html(
        f"""
        <script>
        const text = {payload};
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.94;
        utterance.pitch = 1.0;
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(v =>
          v.name.includes("Google US English") ||
          v.name.includes("Microsoft David") ||
          v.lang === "en-US"
        );
        if (preferred) {{
          utterance.voice = preferred;
        }}
        window.speechSynthesis.speak(utterance);
        </script>
        """,
        height=0,
    )


def load_evaluation_suite() -> dict:
    if not EVALUATION_PATH.exists():
        return {"overview": "", "sections": []}
    return json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))


def chat_tab(session_id: str) -> None:
    st.subheader("Chat")
    st.caption("Synthetic narration only. The app does not try to replicate Andrew Ng's exact voice.")

    history = get_chat_history(session_id, limit=40)
    for item in history:
        with st.chat_message("user" if item["role"] == "user" else "assistant"):
            st.markdown(item["content"])

    prompt = st.chat_input("Ask about machine learning, career transitions, lectures, or Andrew Ng's work")
    if prompt:
        save_message(session_id, "user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking in Andrew-style..."):
                response_text, citations = generate_andrew_response(session_id, prompt)
                save_message(session_id, "model", response_text)
                run_memory_extractor(session_id, prompt, response_text)
            st.markdown(response_text)

            if citations:
                with st.expander("Sources used"):
                    for citation in citations:
                        st.markdown(
                            f"**{citation['title']}**  \n"
                            f"Source: {citation['source']}  \n"
                            f"Similarity: {citation['score']:.2f}"
                        )
                        if citation.get("url"):
                            st.markdown(f"[Open source]({citation['url']})")
                        st.caption(citation["snippet"])

            if st.session_state.get("voice_enabled"):
                clean_text = response_text.replace("```", "").replace("*", "")
                render_speech(clean_text)


def memory_tab(session_id: str) -> None:
    st.subheader("Memory")
    memory = get_memory_state(session_id)
    facts = memory["user_facts"]
    topics = memory["topics_discussed"]

    left, right = st.columns(2)
    with left:
        st.markdown("**User facts**")
        if facts:
            st.table(
                [
                    {"Key": key, "Value": info["value"], "Updated": info["updated_at"]}
                    for key, info in facts.items()
                ]
            )
        else:
            st.info("No user facts stored yet.")

    with right:
        st.markdown("**Topics discussed**")
        if topics:
            st.table(
                [
                    {"Topic": key, "Summary": info["summary"], "Updated": info["timestamp"]}
                    for key, info in topics.items()
                ]
            )
        else:
            st.info("No topics stored yet.")


def sources_tab() -> None:
    st.subheader("Corpus")
    st.caption("Knowledge documents ground answers. Style documents shape tone but should not carry factual claims by themselves.")

    docs = list_corpus_documents()
    if not docs:
        st.warning("No corpus documents were found.")
        return

    bucket_filter = st.radio(
        "Corpus slice",
        options=["all", "knowledge", "style"],
        horizontal=True,
    )
    visible_docs = docs if bucket_filter == "all" else [doc for doc in docs if doc["bucket"] == bucket_filter]

    for doc in visible_docs:
        with st.container(border=True):
            st.markdown(f"**{doc['title']}**")
            meta = f"{doc['bucket'].title()} | {doc['source']} | {doc['word_count']} words"
            if doc["date"]:
                meta += f" | {doc['date']}"
            st.caption(meta)
            if doc["url"]:
                st.markdown(f"[Original source]({doc['url']})")
            st.write(doc["snippet"])


def architecture_tab() -> None:
    st.subheader("Implementation Plan")
    st.markdown(
        """
1. **Corpus layering**: use course transcripts, lecture transcripts, interviews, newsletters, and selected short-form style material.
2. **RAG grounding**: factual retrieval comes from knowledge documents; style retrieval is kept separate and small.
3. **Session-safe memory**: short-term history plus long-term user facts and topic memory keyed by session.
4. **Response generation**: Gemini 2.5 Flash answers in Andrew-style with citations from retrieved chunks.
5. **Synthetic narration**: browser speech synthesis can read the latest answer in a calm, neutral voice.
        """
    )


def evaluation_tab() -> None:
    st.subheader("Evaluation Suite")
    suite = load_evaluation_suite()
    if suite.get("overview"):
        st.caption(suite["overview"])

    for section in suite.get("sections", []):
        with st.container(border=True):
            st.markdown(f"### {section['title']}")
            st.write(section["goal"])

            if section.get("questions"):
                st.markdown("**Evaluation prompts**")
                for index, question in enumerate(section["questions"], start=1):
                    st.markdown(f"{index}. {question}")

            left, right = st.columns(2)
            with left:
                st.markdown("**What a good answer should include**")
                for item in section.get("expected", []):
                    st.markdown(f"- {item}")
            with right:
                st.markdown("**Failure signs**")
                for item in section.get("failure_signs", []):
                    st.markdown(f"- {item}")


def sidebar(session_id: str) -> None:
    st.sidebar.title("Digital Twin Controls")
    st.sidebar.text_input("Session ID", value=session_id, disabled=True)
    st.sidebar.checkbox("Enable synthetic narration", key="voice_enabled")

    if st.sidebar.button("Rebuild vector index", use_container_width=True):
        with st.spinner("Rebuilding index..."):
            build_index()
        st.sidebar.success(f"Index ready at {STORE_PATH}")

    if st.sidebar.button("Reset this session", use_container_width=True):
        reset_session_memory(session_id)
        st.sidebar.success("Session memory cleared.")
        st.rerun()

    st.sidebar.markdown("**Recommended corpus additions**")
    st.sidebar.markdown(
        "- Coursera lecture transcripts\n"
        "- YouTube lecture transcripts\n"
        "- Interviews and keynote transcripts\n"
        "- Blog/newsletter posts\n"
        "- A small style-only folder for short-form tone examples"
    )


def main() -> None:
    session_id = ensure_session_id()
    st.title("Andrew Ng Digital Twin")
    st.caption("Streamlit demo with session-safe memory, grounded retrieval, and synthetic narration.")

    sidebar(session_id)

    chat, memory, sources, evaluation, architecture = st.tabs(
        ["Chat", "Memory", "Sources", "Evaluation", "Architecture"]
    )
    with chat:
        chat_tab(session_id)
    with memory:
        memory_tab(session_id)
    with sources:
        sources_tab()
    with evaluation:
        evaluation_tab()
    with architecture:
        architecture_tab()


if __name__ == "__main__":
    main()
