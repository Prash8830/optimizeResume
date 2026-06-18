"""
LLM router: Groq (primary, 14,400 req/day free) → Gemini (fallback).
All agents call call_llm() — no provider-specific code in agent files.
"""
import os
import time
from typing import Optional
from uuid import uuid4

import google.generativeai as genai
from groq import Groq
from groq import RateLimitError as GroqRateLimitError

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GROQ_MAIN = os.getenv("GROQ_MAIN_MODEL", "llama-3.3-70b-versatile")
GROQ_FAST = os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant")
GEMINI_MAIN = os.getenv("GEMINI_MAIN_MODEL", "gemini-2.5-flash")
GEMINI_FAST = os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash")

_groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
genai.configure(api_key=GEMINI_API_KEY)

# ── LLM observability log ──────────────────────────────────────────────────
_llm_logs: list[dict] = []  # in-memory ring buffer, max 5000 entries
_MAX_LOGS = 5000


def _record(
    provider: str,
    model: str,
    endpoint: str,
    prompt_len: int,
    response_len: int,
    duration_ms: int,
    success: bool,
    error: Optional[str] = None,
):
    entry = {
        "id": str(uuid4()),
        "provider": provider,
        "model": model,
        "endpoint": endpoint,
        "prompt_chars": prompt_len,
        "response_chars": response_len,
        "duration_ms": duration_ms,
        "success": success,
        "error": error,
        "timestamp": time.time(),
    }
    _llm_logs.append(entry)
    if len(_llm_logs) > _MAX_LOGS:
        _llm_logs.pop(0)


def get_llm_logs() -> list[dict]:
    return list(reversed(_llm_logs))


def call_llm(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.3,
    json_mode: bool = False,
    fast: bool = False,
    endpoint: str = "unknown",
    _messages_override: Optional[list[dict]] = None,
) -> str:
    """
    Call Groq first; fall back to Gemini on quota/rate errors.
    Returns the text response string.

    _messages_override: if provided, skip building messages from prompt/system_prompt
    and use this list directly (for chat use cases).
    """
    # Compute prompt_len for logging
    if _messages_override is not None:
        prompt_len = sum(len(m.get("content", "")) for m in _messages_override)
    else:
        prompt_len = len(system_prompt) + len(prompt)

    # ── Groq (primary) ──────────────────────────────────────────────────────
    if _groq_client:
        groq_model = GROQ_FAST if fast else GROQ_MAIN
        t0 = time.time()
        try:
            if _messages_override is not None:
                messages = _messages_override
            else:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

            kwargs: dict = {
                "model": groq_model,
                "messages": messages,
                "temperature": temperature,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            resp = _groq_client.chat.completions.create(**kwargs)
            result = resp.choices[0].message.content or ""
            duration_ms = int((time.time() - t0) * 1000)
            _record("groq", groq_model, endpoint, prompt_len, len(result), duration_ms, True)
            return result
        except GroqRateLimitError:
            duration_ms = int((time.time() - t0) * 1000)
            _record("groq", groq_model, endpoint, prompt_len, 0, duration_ms, False, "RateLimitError")
            print("[llm_router] Groq quota hit — falling back to Gemini")
        except Exception as e:
            duration_ms = int((time.time() - t0) * 1000)
            _record("groq", groq_model, endpoint, prompt_len, 0, duration_ms, False, str(e))
            print(f"[llm_router] Groq error ({type(e).__name__}: {e}) — falling back to Gemini")

    # ── Gemini (fallback) ────────────────────────────────────────────────────
    gemini_model_name = GEMINI_FAST if fast else GEMINI_MAIN
    t0 = time.time()
    try:
        model = genai.GenerativeModel(gemini_model_name)
        gen_cfg = genai.GenerationConfig(
            temperature=temperature,
            **({"response_mime_type": "application/json"} if json_mode else {}),
        )
        if _messages_override is not None:
            # Convert messages list to a single prompt string for Gemini
            full_prompt = "\n".join(
                f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
                for m in _messages_override
            )
        else:
            full_prompt = (system_prompt + "\n\n" + prompt).strip() if system_prompt else prompt

        response = model.generate_content(
            [{"role": "user", "parts": [full_prompt]}],
            generation_config=gen_cfg,
        )
        result = response.text or ""
        duration_ms = int((time.time() - t0) * 1000)
        _record("gemini", gemini_model_name, endpoint, prompt_len, len(result), duration_ms, True)
        return result
    except Exception as e:
        duration_ms = int((time.time() - t0) * 1000)
        _record("gemini", gemini_model_name, endpoint, prompt_len, 0, duration_ms, False, str(e))
        raise
