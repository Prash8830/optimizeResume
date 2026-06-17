import json
import os
import re

import google.generativeai as genai

from app.agents.state import ResumeState

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
_model = genai.GenerativeModel(os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash"))

ATS_THRESHOLD = 0.75
MAX_ITERATIONS = 3


async def ats_checker(state: ResumeState) -> ResumeState:
    resume_lower = state["draft_resume"].lower()
    required_kws = state["jd_analysis"].get("required_keywords", {})

    # Local keyword scan — fast, no LLM
    matched = set()
    missing = set()
    for kw in required_kws:
        kw_lower = kw.lower()
        # Check direct match or stemmed match (e.g. "deploy" matches "deployment")
        if kw_lower in resume_lower or any(kw_lower[:6] in word for word in resume_lower.split()):
            matched.add(kw)
        else:
            missing.add(kw)

    ats_score = len(matched) / len(required_kws) if required_kws else 1.0

    # If below threshold and iterations remain, use LLM to find insertable keywords
    ats_feedback = []
    if ats_score < ATS_THRESHOLD and state.get("iteration_count", 0) < MAX_ITERATIONS and missing:
        feedback_prompt = f"""The following keywords are missing from this resume.
For each keyword, determine if it can be naturally inserted without changing factual meaning.
Return JSON only: {{"insertable": ["kw1", "kw2"], "not_insertable": ["kw3"]}}

Missing keywords: {list(missing)[:10]}

Resume excerpt (first 300 words):
{" ".join(state["draft_resume"].split()[:300])}"""

        try:
            resp = _model.generate_content(
                feedback_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            feedback_data = json.loads(resp.text)
            ats_feedback = feedback_data.get("insertable", [])
        except Exception:
            ats_feedback = list(missing)[:5]

    return {
        **state,
        "ats_score": round(ats_score, 4),
        "ats_feedback": ats_feedback,
    }


def should_loop(state: ResumeState) -> str:
    """LangGraph conditional edge: decide whether to loop back to writer or proceed."""
    if state["ats_score"] < ATS_THRESHOLD and state.get("iteration_count", 0) < MAX_ITERATIONS:
        return "resume_writer"
    return "report_generator"
