"""Configuration for the LLM Council."""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

def parse_key_list(env_var_name: str) -> List[str]:
    """Parse single or comma-separated API keys from env."""
    raw = os.getenv(env_var_name, "").strip()
    if not raw or raw == "your_groq_api_key_here" or raw == "your_gemini_api_key_here":
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]

# Groq API configuration (supports single or comma-separated keys)
GROQ_API_KEYS = parse_key_list("GROQ_API_KEY")
GROQ_API_KEY = GROQ_API_KEYS[0] if GROQ_API_KEYS else os.getenv("GROQ_API_KEY", "")

# Gemini API configuration (Fallback, supports single or comma-separated keys)
GEMINI_API_KEYS = parse_key_list("GEMINI_API_KEY")
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else os.getenv("GEMINI_API_KEY", "")

# Ollama local configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

# 4 Distinct Local Models for 4 Local Agent Roles
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "llama3.2:1b")
MEMBER_A_MODEL = os.getenv("MEMBER_A_MODEL", "qwen2.5:1.5b")
MEMBER_B_MODEL = os.getenv("MEMBER_B_MODEL", "gemma2:2b")
SCORER_MODEL = os.getenv("SCORER_MODEL", "phi3.5:3.8b")

LOCAL_MODELS = [PLANNER_MODEL, MEMBER_A_MODEL, MEMBER_B_MODEL, SCORER_MODEL]

# Model definitions per provider
GROQ_DEFAULT_MODEL = os.getenv("GROQ_DEFAULT_MODEL", "llama-3.1-8b-instant")
GROQ_CHAIRMAN_MODEL = os.getenv("GROQ_CHAIRMAN_MODEL", "llama-3.3-70b-versatile")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash")

# Model Fallback Cascades (tried in order if rate limit / token limit hit)
GROQ_FALLBACK_MODELS = [
    GROQ_CHAIRMAN_MODEL,
    GROQ_DEFAULT_MODEL,
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "qwen-2.5-coder-32b",
    "deepseek-r1-distill-llama-70b"
]

GEMINI_FALLBACK_MODELS = [
    GEMINI_FALLBACK_MODEL,
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

# Council Member Agents
COUNCIL_AGENTS = ["Council Member A", "Council Member B"]

# Chairman Agent
CHAIRMAN_AGENT = "Chairman"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

