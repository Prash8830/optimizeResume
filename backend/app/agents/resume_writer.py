import os

import google.generativeai as genai

from app.agents.state import ResumeState

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
_model = genai.GenerativeModel("gemini-2.0-flash")

SYSTEM_PROMPT = """You are a professional resume writer. Follow these rules strictly:

TRUTHFULNESS RULES (non-negotiable):
1. ONLY use information explicitly present in the source chunks provided.
2. You MAY rephrase using terminology from the job description IF semantically identical to the source.
   Example: source says "built a chatbot" + JD says "conversational AI system" → you may write "built a conversational AI system"
3. You CANNOT add metrics, numbers, outcomes, or technologies NOT present in the source chunks.
4. You CANNOT invent job titles, company names, dates, or projects.
5. You CANNOT claim skills or tools not listed in the source chunks.

FORMAT RULES:
- Plain text output only, no markdown, no # headers, no bullet symbols
- Use these section labels exactly: SUMMARY | EXPERIENCE | PROJECTS | TECHNICAL SKILLS | EDUCATION
- Keep total output under 600 words
- Write experience bullets starting with strong action verbs
- Quantify outcomes only if numbers exist in the source"""

USER_TEMPLATE = """TARGET ROLE: {role_title} at {company}
ROLE TYPE: {role_type}
SENIORITY: {seniority}
COMPANY CONTEXT: {company_context}

REQUIRED KEYWORDS TO INCORPORATE (in order of importance):
{required_keywords}

{ats_feedback_section}

SOURCE CHUNKS — USE ONLY THIS DATA:
{source_chunks}

Write a complete, ATS-optimized resume. Use the required keywords naturally where they accurately describe the source content."""


async def resume_writer(state: ResumeState) -> ResumeState:
    jd = state["jd_analysis"]
    selected = state["selected_content"]

    # Format source chunks for the prompt
    source_parts = []
    for chunk in selected.get("projects", []):
        source_parts.append(f"[PROJECT] {chunk['content']}")
    for chunk in selected.get("experiences", []):
        source_parts.append(f"[EXPERIENCE] {chunk['content']}")
    for chunk in selected.get("skills", []):
        source_parts.append(f"[SKILLS] {chunk['content']}")
    for chunk in selected.get("education", []):
        source_parts.append(f"[EDUCATION] {chunk['content']}")

    # ATS feedback section (for iteration 2+)
    ats_feedback_section = ""
    if state.get("ats_feedback"):
        ats_feedback_section = (
            "ATS FEEDBACK — MISSING KEYWORDS TO WEAVE IN (if truthfully applicable):\n"
            + "\n".join(f"- {kw}" for kw in state["ats_feedback"])
        )

    required_kws = "\n".join(
        f"- {kw} (weight: {w})"
        for kw, w in sorted(jd.get("required_keywords", {}).items(), key=lambda x: -x[1])
    )

    prompt = USER_TEMPLATE.format(
        role_title=state["role_title"],
        company=state["company"],
        role_type=jd.get("role_type", ""),
        seniority=jd.get("seniority", ""),
        company_context=jd.get("company_context", ""),
        required_keywords=required_kws,
        ats_feedback_section=ats_feedback_section,
        source_chunks="\n\n".join(source_parts) if source_parts else "No chunks selected.",
    )

    response = _model.generate_content(
        [{"role": "user", "parts": [SYSTEM_PROMPT + "\n\n" + prompt]}],
        generation_config=genai.GenerationConfig(temperature=0.3),
    )

    return {
        **state,
        "draft_resume": response.text,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }
