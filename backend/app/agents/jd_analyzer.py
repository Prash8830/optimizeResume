import json
import os

import google.generativeai as genai

from app.agents.state import ResumeState

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
_model = genai.GenerativeModel("gemini-2.0-flash")

SYSTEM_PROMPT = """You are a precise job description analyzer. Extract structured data only.
Return valid JSON only — no markdown, no code fences, no explanation.

Weight rules:
- Keywords in job title: 3.0
- Keywords under "required" / "must have" / "you will": 2.0
- Keywords under "preferred" / "nice to have" / "bonus": 1.0
- All other mentioned technical terms: 1.0"""

USER_TEMPLATE = """Analyze this job description for the role: {role_title} at {company}

{job_description}

Return this exact JSON structure:
{{
  "role_type": "<one of: MLOps|GenAI|Agentic AI|Conversational AI|Full-stack|Data Science|Backend|Other>",
  "seniority": "<Junior|Mid|Senior|Lead>",
  "required_keywords": {{"keyword": weight_float}},
  "preferred_keywords": {{"keyword": weight_float}},
  "company_context": "<one sentence about the company tech culture or product focus>"
}}"""


async def jd_analyzer(state: ResumeState) -> ResumeState:
    prompt = USER_TEMPLATE.format(
        role_title=state["role_title"],
        company=state["company"],
        job_description=state["job_description"],
    )

    response = _model.generate_content(
        [{"role": "user", "parts": [SYSTEM_PROMPT + "\n\n" + prompt]}],
        generation_config=genai.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )

    try:
        jd_analysis = json.loads(response.text)
    except json.JSONDecodeError:
        # Fallback: extract keywords naively from JD text
        words = state["job_description"].lower().split()
        jd_analysis = {
            "role_type": "Other",
            "seniority": "Mid",
            "required_keywords": {w: 1.0 for w in set(words) if len(w) > 4},
            "preferred_keywords": {},
            "company_context": "",
        }

    return {**state, "jd_analysis": jd_analysis}
