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

# Enable CORS for frontend development and Vercel deployments
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
    """Safely check Ollama reachability on startup without throwing exceptions on serverless environments."""
    try:
        is_reachable = await asyncio.wait_for(check_ollama_reachable(), timeout=2.0)
        if is_reachable:
            logger.info("Ollama server reached successfully. Warming up local models...")
            await warmup_local_models()
        else:
            logger.info("Local Ollama server not reached. Cloud fallbacks (Groq/Gemini) will be used.")
    except Exception as e:
        logger.info(f"Serverless/Cloud environment detected or Ollama check skipped: {e}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "6-Agent LLM Council API"}


@app.get("/api/health")
async def health_check():
    """Explicit API health check endpoint."""
    return {"status": "ok", "service": "6-Agent LLM Council API"}


@app.post("/api/council/run")
async def run_council_api(body: StartCouncilRequest, background_tasks: BackgroundTasks):
    """
    POST /api/council/run
    Starts a council debate run in background and returns request_id immediately.
    """
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    request_id = str(uuid.uuid4())

    async def _run():
        try:
            await execute_council_run(user_query=question, request_id=request_id)
        except Exception as e:
            logger.error(f"Error in background council run {request_id}: {e}")

    background_tasks.add_task(_run)

    return {
        "request_id": request_id,
        "message": f"Council run initiated for query: '{question}'"
    }


@app.get("/api/council/state/{request_id}")
async def get_council_state_api(request_id: str):
    """GET /api/council/state/{request_id} - Fetches current state of a council run."""
    state = get_council_state(request_id)
    if not state:
        raise HTTPException(status_code=404, detail="Request ID not found.")
    return state


@app.websocket("/ws/council/{request_id}")
async def websocket_council_endpoint(websocket: WebSocket, request_id: str):
    """WebSocket endpoint for real-time live streaming of council deliberation status updates."""
    await websocket.accept()

    if request_id not in _WEBSOCKET_CONNECTIONS:
        _WEBSOCKET_CONNECTIONS[request_id] = []
    _WEBSOCKET_CONNECTIONS[request_id].append(websocket)

    def _broadcast_to_ws(entry: Dict[str, Any]):
        if entry.get("request_id") == request_id or not entry.get("request_id"):
            dead_ws = []
            for ws in _WEBSOCKET_CONNECTIONS.get(request_id, []):
                try:
                    asyncio.create_task(ws.send_text(json.dumps(entry)))
                except Exception:
                    dead_ws.append(ws)
            for ws in dead_ws:
                if ws in _WEBSOCKET_CONNECTIONS.get(request_id, []):
                    _WEBSOCKET_CONNECTIONS[request_id].remove(ws)

    register_status_callback(_broadcast_to_ws)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket error for {request_id}: {e}")
    finally:
        unregister_status_callback(_broadcast_to_ws)
        if request_id in _WEBSOCKET_CONNECTIONS and websocket in _WEBSOCKET_CONNECTIONS[request_id]:
            _WEBSOCKET_CONNECTIONS[request_id].remove(websocket)
