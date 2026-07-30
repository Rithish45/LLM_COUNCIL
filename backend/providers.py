"""Unified LLM Provider module for Groq, Gemini, and Ollama with JSON parsing, fallbacks, and live status callbacks."""

import os
import time
import json
import logging
import asyncio
import httpx
from typing import List, Dict, Any, Optional, Callable, Tuple

from .config import (
    GROQ_API_KEY,
    GEMINI_API_KEY,
    GROQ_API_KEYS,
    GEMINI_API_KEYS,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    PLANNER_MODEL,
    MEMBER_A_MODEL,
    MEMBER_B_MODEL,
    SCORER_MODEL,
    LOCAL_MODELS,
    GROQ_DEFAULT_MODEL,
    GROQ_CHAIRMAN_MODEL,
    GEMINI_FALLBACK_MODEL,
    GROQ_FALLBACK_MODELS,
    GEMINI_FALLBACK_MODELS,
)

logger = logging.getLogger("llm_council")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Mapping of the 4 local agent roles to (Model Name, max num_predict tokens, hard timeout in seconds)
LOCAL_ROLE_CONFIG = {
    "Planner": (PLANNER_MODEL, 150, 8.0),
    "Council Member A": (MEMBER_A_MODEL, 300, 8.0),
    "Council Member B": (MEMBER_B_MODEL, 300, 8.0),
    "Disagreement Scorer": (SCORER_MODEL, 150, 8.0),
}

# Global streaming / status callback for WebSockets broadcast
_status_callbacks: List[Callable[[Dict[str, Any]], None]] = []

def register_status_callback(cb: Callable[[Dict[str, Any]], None]):
    """Register a callback for real-time agent status broadcasts."""
    if cb not in _status_callbacks:
        _status_callbacks.append(cb)

def unregister_status_callback(cb: Callable[[Dict[str, Any]], None]):
    """Unregister a callback."""
    if cb in _status_callbacks:
        _status_callbacks.remove(cb)

def _broadcast_status(entry: Dict[str, Any]):
    """Helper to broadcast agent status updates."""
    for cb in list(_status_callbacks):
        try:
            cb(entry)
        except Exception as e:
            logger.warning(f"Error in status callback: {e}")


async def check_ollama_reachable(timeout: float = 3.0) -> bool:
    """Check if local Ollama server is reachable. Fail fast at startup if not."""
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            return resp.status_code == 200
    except Exception:
        return False


async def warmup_local_models() -> Dict[str, int]:
    """Send a throwaway warm-up prompt to each of the 4 local models on startup so Ollama loads them into VRAM."""
    results = {}
    for role, (model_name, num_pred, t_out) in LOCAL_ROLE_CONFIG.items():
        start = time.perf_counter()
        try:
            await _call_ollama(
                model=model_name,
                messages=[{"role": "user", "content": "ping"}],
                num_predict=5,
                timeout=12.0,
                stream=False
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.info(f"[WARMUP] Warmed up {role} ({model_name}) in {elapsed_ms}ms")
            results[role] = elapsed_ms
        except Exception as e:
            logger.warning(f"[WARMUP] Failed/skipped warm up for {role} ({model_name}): {e}")
            results[role] = -1
    return results


async def _call_groq(model: str, messages: List[Dict[str, str]], api_key: str = None, timeout: float = 60.0) -> Dict[str, Any]:
    """Call Groq API (OpenAI-compatible) with specified model and API key."""
    key = api_key or (GROQ_API_KEYS[0] if GROQ_API_KEYS else GROQ_API_KEY)
    if not key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message'].get('content', '')
        return {"content": content}


async def _call_gemini(model: str, messages: List[Dict[str, str]], api_key: str = None, timeout: float = 60.0) -> Dict[str, Any]:
    """Call Gemini API (Google AI Studio OpenAI-compatible endpoint) with specified model and API key."""
    key = api_key or (GEMINI_API_KEYS[0] if GEMINI_API_KEYS else GEMINI_API_KEY)
    if not key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message'].get('content', '')
        return {"content": content}


async def _call_ollama(
    model: str,
    messages: List[Dict[str, str]],
    num_predict: int = 300,
    timeout: float = 8.0,
    stream: bool = True
) -> Dict[str, Any]:
    """Call local Ollama API with streaming and num_predict token limits."""
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {
            "num_predict": num_predict
        }
    }
    
    if stream:
        content_chunks = []
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            delta = chunk.get("message", {}).get("content", "")
                            if delta:
                                content_chunks.append(delta)
                        except Exception:
                            pass
        full_content = "".join(content_chunks)
        return {"content": full_content}
    else:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get('message', {}).get('content', '')
            return {"content": content}


async def _try_cloud_providers(
    agent_name: str,
    messages: List[Dict[str, str]],
    primary_model: str,
    timeout: float = 60.0,
    request_id: Optional[str] = None
) -> Tuple[str, str, str, str, bool]:
    """
    Cascade through available Groq keys & fallback models, then Gemini keys & fallback models.
    Returns: (content, status, provider_used, model_used, fallback_triggered)
    """
    fallback_triggered = False

    # Build Groq model order starting with primary_model
    groq_models = [primary_model] + [m for m in GROQ_FALLBACK_MODELS if m != primary_model]
    groq_keys = GROQ_API_KEYS or ([GROQ_API_KEY] if GROQ_API_KEY else [])

    if groq_keys:
        for model in groq_models:
            for key in groq_keys:
                try:
                    res = await _call_groq(model=model, messages=messages, api_key=key, timeout=timeout)
                    content = res.get("content", "")
                    if content:
                        return content, "success", "groq", model, fallback_triggered
                except Exception as e:
                    fallback_triggered = True
                    logger.warning(
                        f"Groq call failed for agent '{agent_name}' with model '{model}': {e}. Retrying next key/model..."
                    )
                    _broadcast_status({
                        "request_id": request_id,
                        "agent": agent_name,
                        "status": "rate_limit_failover",
                        "provider": "groq",
                        "model": model,
                        "error": str(e),
                        "timestamp": time.time()
                    })

    # If Groq fails or no keys configured -> Failover to Gemini
    fallback_triggered = True
    gemini_models = GEMINI_FALLBACK_MODELS
    gemini_keys = GEMINI_API_KEYS or ([GEMINI_API_KEY] if GEMINI_API_KEY else [])

    if gemini_keys:
        for model in gemini_models:
            for key in gemini_keys:
                try:
                    res = await _call_gemini(model=model, messages=messages, api_key=key, timeout=timeout)
                    content = res.get("content", "")
                    if content:
                        logger.info(f"Gemini failover succeeded for agent '{agent_name}' with model '{model}'")
                        return content, "success", "gemini", model, True
                except Exception as e:
                    logger.warning(
                        f"Gemini fallback failed for agent '{agent_name}' with model '{model}': {e}. Retrying next key/model..."
                    )
                    _broadcast_status({
                        "request_id": request_id,
                        "agent": agent_name,
                        "status": "rate_limit_failover",
                        "provider": "gemini",
                        "model": model,
                        "error": str(e),
                        "timestamp": time.time()
                    })

    # Ultimate fallback if all APIs are exhausted/unreachable
    return (
        f"[{agent_name} Cached Fallback] All available LLM API keys or model token limits were hit. Operating in fallback mode.",
        "cached",
        "cached",
        "system-fallback",
        True
    )


async def call_agent(
    agent_name: str,
    messages: List[Dict[str, str]],
    timeout: Optional[float] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified entry point for ALL agent LLM calls.
    Routes local roles (Planner, Member A, Member B, Scorer) to Ollama with strict token limits and low timeouts,
    or cloud providers (Groq primary, Gemini fallback) for Fact Grounder & Chairman.
    """
    start_time = time.perf_counter()
    
    # Broadcast 'starting' status
    _broadcast_status({
        "request_id": request_id,
        "agent": agent_name,
        "status": "running",
        "timestamp": time.time()
    })

    # Check if this role is configured as a local Ollama agent
    if agent_name in LOCAL_ROLE_CONFIG:
        model_used, num_pred, default_timeout = LOCAL_ROLE_CONFIG[agent_name]
        call_timeout = timeout if timeout is not None else default_timeout
        ollama_ok = await check_ollama_reachable(timeout=2.0)
        
        if ollama_ok:
            try:
                res = await _call_ollama(
                    model=model_used,
                    messages=messages,
                    num_predict=num_pred,
                    timeout=call_timeout,
                    stream=True
                )
                content = res.get("content", "")
                if content:
                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    log_entry = {
                        "request_id": request_id,
                        "agent": agent_name,
                        "provider": "ollama",
                        "model": model_used,
                        "latency_ms": latency_ms,
                        "fallback_triggered": False,
                        "status": "success",
                        "content": content,
                        "timestamp": time.time()
                    }
                    _broadcast_status(log_entry)
                    return {
                        "content": content,
                        "status": "success",
                        "agent": agent_name,
                        "provider": "ollama",
                        "model": model_used,
                        "latency_ms": latency_ms,
                        "fallback_triggered": False
                    }
            except Exception as e:
                logger.warning(f"Local Ollama call failed/timed out for agent '{agent_name}' ({model_used}): {e}. Falling back to cloud...")

        # If Ollama failed or not reachable, fallback to cloud providers (Groq -> Gemini)
        content, status, provider_used, model_used, fallback_triggered = await _try_cloud_providers(
            agent_name=agent_name,
            messages=messages,
            primary_model=GROQ_DEFAULT_MODEL,
            timeout=timeout or 60.0,
            request_id=request_id
        )

    else:
        # Cloud agents (Fact Grounder, Chairman)
        primary_model = GROQ_CHAIRMAN_MODEL if agent_name == "Chairman" else GROQ_DEFAULT_MODEL
        cloud_timeout = timeout if timeout is not None else 60.0

        content, status, provider_used, model_used, fallback_triggered = await _try_cloud_providers(
            agent_name=agent_name,
            messages=messages,
            primary_model=primary_model,
            timeout=cloud_timeout,
            request_id=request_id
        )

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    log_entry = {
        "request_id": request_id,
        "agent": agent_name,
        "provider": provider_used,
        "model": model_used,
        "latency_ms": latency_ms,
        "fallback_triggered": fallback_triggered,
        "status": status,
        "content": content,
        "timestamp": time.time()
    }
    logger.info(
        f"[LLM CALL] Agent: {agent_name} | Provider: {provider_used} | Model: {model_used} | "
        f"Latency: {latency_ms}ms | Fallback: {fallback_triggered} | Status: {status}"
    )
    _broadcast_status(log_entry)
    
    return {
        "content": content,
        "status": status,
        "agent": agent_name,
        "provider": provider_used,
        "model": model_used,
        "latency_ms": latency_ms,
        "fallback_triggered": fallback_triggered
    }



def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Helper to extract JSON object or list from text markdown."""
    text = text.strip()
    if text.startswith("```"):
        # Strip markdown code blocks
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    
    # Locate first '{' or '[' and last '}' or ']'
    start_brace = text.find("{")
    start_bracket = text.find("[")
    
    if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
        end_brace = text.rfind("}")
        if end_brace != -1:
            text = text[start_brace:end_brace+1]
    elif start_bracket != -1:
        end_bracket = text.rfind("]")
        if end_bracket != -1:
            text = text[start_bracket:end_bracket+1]

    try:
        return json.loads(text)
    except Exception:
        return None


async def call_agent_json(
    agent_name: str,
    messages: List[Dict[str, str]],
    default_factory: Callable[[], Any],
    timeout: Optional[float] = None,
    request_id: Optional[str] = None
) -> Tuple[Any, Dict[str, Any]]:
    """
    Call agent expecting a JSON output.
    If malformed JSON is returned, retries once with reinforced JSON instruction.
    If retry also fails, uses default_factory() output and logs failure.

    Returns:
        Tuple of (parsed_json_obj, raw_response_dict)
    """
    res = await call_agent(agent_name, messages, timeout=timeout, request_id=request_id)
    raw_content = res.get("content", "")
    parsed = _extract_json(raw_content)

    if parsed is not None:
        return parsed, res

    logger.warning(f"Malformed JSON from agent '{agent_name}'. Retrying once with JSON reinforcement...")
    
    # Retry once with reinforced prompt
    retry_messages = list(messages) + [
        {"role": "assistant", "content": raw_content},
        {
            "role": "user",
            "content": "CRITICAL: Your previous response was NOT valid JSON. Output ONLY raw, valid JSON. No conversational text or markdown explanation around it."
        }
    ]
    
    res_retry = await call_agent(agent_name, retry_messages, timeout=timeout, request_id=request_id)
    parsed_retry = _extract_json(res_retry.get("content", ""))

    if parsed_retry is not None:
        return parsed_retry, res_retry

    logger.error(f"Retry also failed for JSON parsing in agent '{agent_name}'. Using default fallback structure.")
    return default_factory(), res_retry
