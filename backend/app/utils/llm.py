"""
LLM router: Groq (primary, 14,400 req/day free) → Gemini (fallback).
All agents call call_llm() — no provider-specific code in agent files.
"""
import json
import os

import google.generativeai as genai
from groq import Groq
from groq import RateLimitError as GroqRateLimitError
from google.api_core.exceptions import ResourceExhausted

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GROQ_MAIN = os.getenv("GROQ_MAIN_MODEL", "llama-3.3-70b-versatile")
GROQ_FAST = os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant")
GEMINI_MAIN = os.getenv("GEMINI_MAIN_MODEL", "gemini-2.5-flash")
GEMINI_FAST = os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash")

_groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
genai.configure(api_key=GEMINI_API_KEY)


def call_llm(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.3,
    json_mode: bool = False,
    fast: bool = False,
) -> str:
    """
    Call Groq first; fall back to Gemini on quota/rate errors.
    Returns the text response string.
    """
    # ── Groq (primary) ──────────────────────────────────────────────────────
    if _groq_client:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            kwargs: dict = {
                "model": GROQ_FAST if fast else GROQ_MAIN,
                "messages": messages,
                "temperature": temperature,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            resp = _groq_client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except GroqRateLimitError:
            print("[llm_router] Groq quota hit — falling back to Gemini")
        except Exception as e:
            print(f"[llm_router] Groq error ({type(e).__name__}: {e}) — falling back to Gemini")

    # ── Gemini (fallback) ────────────────────────────────────────────────────
    model_name = GEMINI_FAST if fast else GEMINI_MAIN
    model = genai.GenerativeModel(model_name)
    gen_cfg = genai.GenerationConfig(
        temperature=temperature,
        **({"response_mime_type": "application/json"} if json_mode else {}),
    )
    full_prompt = (system_prompt + "\n\n" + prompt).strip() if system_prompt else prompt
    response = model.generate_content(
        [{"role": "user", "parts": [full_prompt]}],
        generation_config=gen_cfg,
    )
    return response.text or ""
