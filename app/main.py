import time
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.context_resolution import resolve_contextual_references
from app.decision_engine import decide_response
from app.fast_path import detect_fast_path
from app.memory import SQLiteSessionStore
from app.models import (
    ChatRequest,
    ChatResponse,
    SessionRenameRequest,
    SessionSummary,
    StoredMessage,
)
from app.responder_factory import build_responder


app = FastAPI(title="DoubtGPT API", version="0.1.0")
settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
session_store = SQLiteSessionStore(db_path=settings.database_path)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    provider_status = "configured"
    if settings.llm_provider == "gemini" and not settings.gemini_api_key:
        provider_status = "missing_api_key"
    if settings.llm_provider == "ollama":
        provider_status = "configured_local"
    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "provider_status": provider_status,
        "database_path": settings.database_path,
        "gemini_sample_count": str(settings.gemini_sample_count),
        "ollama_model": settings.ollama_model,
        "ollama_sample_count": str(settings.ollama_sample_count),
        "semantic_agreement_enabled": str(settings.semantic_agreement_enabled).lower(),
        "embedding_model_name": settings.embedding_model_name,
        "ollama_embed_model": settings.ollama_embed_model,
        "fast_path_enabled": str(settings.fast_path_enabled).lower(),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    history = session_store.get_history(request.session_id)
    started_at = time.perf_counter()
    result = None
    resolved_message, resolution_debug = resolve_contextual_references(
        request.message,
        history,
    )

    if settings.fast_path_enabled:
        result = detect_fast_path(resolved_message, history)

    try:
        if result is None:
            responder = build_responder(settings)
            result = responder.generate(resolved_message, history)
    except Exception as exc:
        result = decide_response(resolved_message, history)
        result["reason"] = (
            f"{result['reason']} Fallback responder used because provider setup failed: {exc}"
        )
        result["debug"] = {
            **result.get("debug", {}),
            "fast_path": False,
            "fallback_used": True,
        }

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    result["debug"] = {
        **result.get("debug", {}),
        "latency_ms": duration_ms,
        "fast_path": result.get("debug", {}).get("fast_path", False),
    }
    if resolution_debug is not None:
        result["debug"] = {
            **result["debug"],
            **resolution_debug,
        }

    session_store.add_turn(request.session_id, "user", request.message)
    session_store.add_turn(
        request.session_id,
        "assistant",
        str(result["response"]),
        decision=getattr(result["decision"], "value", str(result["decision"])),
        confidence=float(result["confidence"]),
        reason=str(result["reason"]),
        debug=result.get("debug"),
    )

    return ChatResponse(
        decision=result["decision"],
        confidence=result["confidence"],
        response=str(result["response"]),
        reason=str(result["reason"]),
        session_id=request.session_id,
        debug=result.get("debug") if request.include_debug else None,
    )


@app.get("/sessions/{session_id}/messages", response_model=list[StoredMessage])
def get_session_messages(session_id: str) -> list[StoredMessage]:
    messages = session_store.get_session_messages(session_id)
    return [StoredMessage(**message) for message in messages]


@app.get("/sessions", response_model=list[SessionSummary])
def list_sessions() -> list[SessionSummary]:
    sessions = session_store.list_sessions()
    return [SessionSummary(**session) for session in sessions]


@app.patch("/sessions/{session_id}", status_code=204)
def rename_session(session_id: str, request: SessionRenameRequest) -> Response:
    session_store.rename_session(session_id, request.title)
    return Response(status_code=204)


@app.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str) -> Response:
    session_store.delete_session(session_id)
    return Response(status_code=204)
