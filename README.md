# Andrew Ng Digital Twin

Andrew Ng Digital Twin is a Streamlit-based AI assistant that emulates Andrew Ng's teaching style using Gemini-powered retrieval, session memory, and a curated corpus of lectures, research, and public writing.

## Core Features

- **Andrew-style responses** using Gemini 2.5 Flash
- **RAG grounding** using Gemini embeddings and a local vector store
- **Session-based memory** stored in SQLite
- **Knowledge corpus** for factual grounding
- **Style corpus** for tone and communication patterns
- **Synthetic narration** through browser speech synthesis
- **Evaluation suite** for persona, accuracy, grounding, memory, and timeline testing

## Project Structure

- [app.py](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\app.py): Streamlit user interface
- [run.py](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\run.py): app launcher
- [backend](C:\Users\Nishant Varshney\OneDrive\Desktop%digital%20twin\backend): retrieval, memory, corpus, and response logic
- [data/corpus](C:\Users\Nishant Varshney\OneDrive\Desktop%digital%20twin\data\corpus): knowledge and style documents
- [data/evaluation](C:\Users\Nishant Varshney\OneDrive\Desktop%digital%20twin\data\evaluation): evaluation suite data
- [data/conversations](C:\Users\Nishant Varshney\OneDrive\Desktop%digital%20twin\data\conversations): sample conversations

## Corpus Layout

Store factual material in:
- `data/corpus/knowledge/`

Examples:
- lecture transcripts
- course transcripts
- research summaries
- papers
- interviews
- newsletters and blogs

Store tone material in:
- `data/corpus/style/`

Examples:
- short public posts
- recurring phrases
- teaching-style notes

## App Sections

- **Chat**: talk to the digital twin
- **Memory**: inspect stored user facts and discussed topics
- **Sources**: browse the current corpus
- **Evaluation**: review the built-in quality checklist
- **Architecture**: see the high-level system plan

## Setup

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add a root `.env` file:

```env
GEMINI_API_KEY=your_key_here
```

## Run

```bash
python run.py
```

Or directly:

```bash
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## Voice

The app supports synthetic browser narration for responses.

## Important Files

- [backend/agent.py](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\backend\agent.py)
- [backend/rag.py](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\backend\rag.py)
- [backend/memory.py](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\backend\memory.py)
- [backend/corpus.py](C:\Users\Nishant Varshney\OneDrive\Desktop\digital%20twin\backend\corpus.py)

