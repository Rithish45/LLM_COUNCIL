"""FastAPI backend with WebSockets live streaming for the 6-agent LLM Council."""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio
import logging

from .providers import check_ollama_reachable, warmup_local_models, register_status_callback, unregister_status_callback
from .council import execute_council_run, get_council_state

logger = logging.getLogger("llm_council.api")

app = FastAPI(title="6-Agent LLM Council API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartCouncilRequest(BaseModel):
    question: str


class StartCouncilResponse(BaseModel):
    request_id: str
    message: str


# Active WebSocket connections per request_id
_WEBSOCKET_CONNECTIONS: Dict[str, List[WebSocket]] = {}


@app.on_event("startup")
async def startup_event():
    """Fail fast at startup if local Ollama server is unreachable and warm up all 4 local models in VRAM."""
    is_reachable = await check_ollama_reachable()
    if not is_reachable:
        logger.warning(
            "OLLAMA WARNING: Local Ollama server is currently unreachable at configured OLLAMA_BASE_URL."
        )
    else:
        logger.info("Ollama server reached successfully. Warming up all 4 local models into VRAM...")
        warmup_res = await warmup_local_models()
        logger.info(f"Warmup results (ms per agent role): {warmup_res}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "6-Agent LLM Council API"}


@app.get("/api/health")
async def health_check():
    """Diagnostic health check."""
    ollama_ok = await check_ollama_reachable()
    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama_reachable": ollama_ok
    }


@app.post("/api/council/run", response_model=StartCouncilResponse)
async def start_council_run(request: StartCouncilRequest, background_tasks: BackgroundTasks):
    """
    Start a new multi-round council run in the background.
    Returns request_id immediately for WebSocket streaming and result polling.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    request_id = str(uuid.uuid4())

    # Dispatch council run in background task
    background_tasks.add_task(run_and_notify_websockets, request.question, request_id)

    return StartCouncilResponse(
        request_id=request_id,
        message="Council run initiated successfully."
    )


async def run_and_notify_websockets(question: str, request_id: str):
    """Execute council run and stream events via WebSockets."""
    # Callback to stream events directly to connected WebSockets
    def ws_broadcast(entry: Dict[str, Any]):
        if entry.get("request_id") == request_id and request_id in _WEBSOCKET_CONNECTIONS:
            connections = list(_WEBSOCKET_CONNECTIONS[request_id])
            for ws in connections:
                try:
                    asyncio.create_task(ws.send_text(json.dumps(entry)))
                except Exception as e:
                    logger.warning(f"Error sending WebSocket message: {e}")

    register_status_callback(ws_broadcast)
    try:
        await execute_council_run(question, request_id=request_id)
        # Send completion event
        if request_id in _WEBSOCKET_CONNECTIONS:
            final_state = get_council_state(request_id)
            for ws in list(_WEBSOCKET_CONNECTIONS[request_id]):
                try:
                    await ws.send_text(json.dumps({
                        "request_id": request_id,
                        "status": "completed",
                        "final_state": final_state
                    }))
                except Exception:
                    pass
    finally:
        unregister_status_callback(ws_broadcast)


@app.get("/api/council/result/{request_id}")
async def get_council_result(request_id: str):
    """Get complete state object for a given request_id."""
    state = get_council_state(request_id)
    if not state:
        raise HTTPException(status_code=404, detail="Council run request_id not found.")
    return state


@app.websocket("/ws/council/{request_id}")
async def websocket_endpoint(websocket: WebSocket, request_id: str):
    """WebSocket stream of live agent execution logs and text streaming."""
    await websocket.accept()
    if request_id not in _WEBSOCKET_CONNECTIONS:
        _WEBSOCKET_CONNECTIONS[request_id] = []
    _WEBSOCKET_CONNECTIONS[request_id].append(websocket)

    # Send current accumulated logs on initial connection
    existing_state = get_council_state(request_id)
    if existing_state and existing_state.get("agent_status_log"):
        for entry in existing_state["agent_status_log"]:
            await websocket.send_text(json.dumps(entry))

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        if request_id in _WEBSOCKET_CONNECTIONS and websocket in _WEBSOCKET_CONNECTIONS[request_id]:
            _WEBSOCKET_CONNECTIONS[request_id].remove(websocket)
