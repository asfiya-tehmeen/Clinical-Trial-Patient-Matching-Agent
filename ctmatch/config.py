"""
config.py
=========
Shared configuration and helpers for the Clinical Trial Patient Matching Agent.

Holds:
  - Lazy Groq (OpenAI-compatible) client; the key comes from the environment
  - Model and pipeline configuration constants
  - call_llm()  — unified LLM call
  - clean_json() — robust JSON parsing for LLM output

The API key is read from the GROQ_API_KEY environment variable, or from a
.env file in the current directory / the user's home (~/.ctmatch.env).
Get a free key at https://console.groq.com
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()                                   # ./.env
load_dotenv(Path.home() / ".ctmatch.env")       # per-user fallback

# ------------------------------------------------------------------
# Model config
# ------------------------------------------------------------------
# Use the fast model for cheap steps (extraction, summaries).
# Use the reasoning model for deep steps (criteria analysis).
MODEL_FAST      = os.getenv("CTMATCH_MODEL_FAST", "llama-3.1-8b-instant")
MODEL_REASONING = os.getenv("CTMATCH_MODEL_REASONING", "llama-3.3-70b-versatile")

# ------------------------------------------------------------------
# Pipeline config
# ------------------------------------------------------------------
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
CTGOV_URL     = "https://clinicaltrials.gov/api/v2/studies"
MAX_TRIALS    = 25    # trials fetched before LLM reasoning
TOP_K         = 5     # top matches shown in final output


class MissingAPIKeyError(RuntimeError):
    pass


_client = None


def get_client() -> OpenAI:
    """Build the Groq client on first use so imports never require a key."""
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY", "").strip()
        if not key:
            raise MissingAPIKeyError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com, "
                "then run `ctmatch init` or set the GROQ_API_KEY environment variable."
            )
        _client = OpenAI(api_key=key, base_url=GROQ_BASE_URL, max_retries=5)
    return _client


# ------------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------------
def call_llm(prompt: str, model: str, max_tokens: int = 1500) -> str:
    """Unified LLM API call — returns response text."""
    response = get_client().chat.completions.create(
        model      = model,
        max_tokens = max_tokens,
        messages   = [{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def clean_json(raw: str) -> dict:
    """Strip markdown fences if the model wraps output in them, then parse JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
