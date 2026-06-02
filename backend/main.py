from typing import Any, Dict, List

import dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent import generate_andrew_response, run_memory_extractor
from backend.corpus import list_corpus_documents
from backend.memory import (
    get_chat_history,
    get_memory_state,
    reset_all_memories,
    reset_session_memory,
    save_message,
)

dotenv.load_dotenv()

app = FastAPI(title="Andrew Ng Digital Twin API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    citations: List[Dict[str, Any]]


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        save_message(request.session_id, "user", request.message)
        response_text, citations = generate_andrew_response(request.session_id, request.message)
        save_message(request.session_id, "model", response_text)
        background_tasks.add_task(run_memory_extractor, request.session_id, request.message, response_text)
        return ChatResponse(response=response_text, citations=citations)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/memory")
async def memory_endpoint(session_id: str = Query(...)) -> Dict[str, Any]:
    return get_memory_state(session_id)


@app.get("/api/history")
async def history_endpoint(session_id: str = Query(...)) -> List[Dict[str, str]]:
    return get_chat_history(session_id)


@app.post("/api/reset")
async def reset_endpoint(session_id: str | None = None) -> Dict[str, str]:
    if session_id:
        reset_session_memory(session_id)
        return {"status": "success", "message": f"Session {session_id} cleared."}

    reset_all_memories()
    return {"status": "success", "message": "All memories cleared."}


@app.get("/api/corpus")
async def corpus_endpoint() -> List[Dict[str, Any]]:
    return list_corpus_documents()
