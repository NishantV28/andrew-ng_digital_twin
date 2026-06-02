# Andrew Ng Digital Twin

This project is now centered on a simpler, more reliable **Streamlit demo** for an Andrew Ng-inspired digital twin.

It keeps the useful parts of the original idea:
- Gemini 2.5 Flash for response generation
- Gemini embeddings for retrieval
- a session-scoped memory layer in SQLite
- a grounded corpus with room for lecture transcripts, interviews, course material, and style notes

## What changed

The React frontend has been replaced in the main workflow by a Streamlit app so the demo is easier to run and easier to present.

The backend has also been cleaned up:
- long-term memory is now scoped by `session_id`
- chat history loads the **most recent** turns instead of the oldest ones
- the current user turn is no longer duplicated inside the model prompt
- corpus handling supports separate `knowledge` and `style` documents

## Recommended corpus expansion

Add more `.txt` files under:
- `data/corpus/knowledge/`
- `data/corpus/style/`

Use `knowledge` for:
- Coursera transcripts
- YouTube lecture transcripts
- keynote/interview transcripts
- papers, blog posts, newsletters

Use `style` for:
- short tone examples
- recurring phrases
- teaching-pattern notes

Keep factual grounding in `knowledge`. Use `style` only to shape tone.

## Run

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add a root `.env` file:

```env
GEMINI_API_KEY=your_key_here
```

4. Start the app:

```bash
python run.py
```

Or directly:

```bash
streamlit run app.py
```

## App sections

- **Chat**: converse with the twin
- **Memory**: inspect session-scoped user facts and topics
- **Sources**: review corpus documents and their metadata
- **Evaluation**: run the built-in quality checklist for persona, RAG, memory, and timeline awareness
- **Architecture**: high-level implementation notes

## Voice

The app supports **synthetic browser narration** for responses.

It does **not** attempt to clone Andrew Ng's real voice.

## Files to focus on

- [app.py](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\app.py)
- [backend/agent.py](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\backend\agent.py)
- [backend/rag.py](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\backend\rag.py)
- [backend/memory.py](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\backend\memory.py)
- [backend/corpus.py](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\backend\corpus.py)

## Additional docs

- [DELIVERABLE_REPORT.md](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\DELIVERABLE_REPORT.md)
- [PROJECT_WALKTHROUGH.md](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\PROJECT_WALKTHROUGH.md)
