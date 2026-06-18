from app.agents.state import ResumeState
from app.utils.llm import call_llm

SYSTEM_PROMPT = """You are a professional resume writer. Follow these rules strictly:

TRUTHFULNESS RULES (non-negotiable):
1. ONLY use information explicitly present in the source chunks provided.
2. You MAY rephrase using terminology from the job description IF semantically identical to the source.
3. You CANNOT add metrics, numbers, outcomes, or technologies NOT present in the source chunks.
4. You CANNOT invent job titles, company names, dates, or projects.
5. You CANNOT claim skills or tools not listed in the source chunks.

FORMAT RULES:
- Plain text output only, no markdown, no # headers, no bullet symbols
- Use these section labels exactly (one per line): SUMMARY | EXPERIENCE | PROJECTS | TECHNICAL SKILLS | EDUCATION
- CRITICAL: Keep total output under 480 words — this must fit on ONE page
- Section order: SUMMARY → TECHNICAL SKILLS → EXPERIENCE → PROJECTS → EDUCATION

SUMMARY:
- Write 3-4 sentences. First sentence: years of experience + domain + key specialization. Second: 2-3 specific technologies used. Third: a concrete outcome or client impact from the source.

TECHNICAL SKILLS:
- Group by category, one line each: "Category: skill1, skill2, skill3"
- Include ALL skills present in the source chunks — do not omit any
- Never list a skill identical to its category name alone — merge into a related category
- Aim for 5-7 skill categories to demonstrate breadth

EXPERIENCE:
- FIRST LINE of each job MUST be: "Role Title at Company Name" (e.g. "AI Engineer – Generative AI at Tata Consultancy Services (TCS)")
- Then list achievement bullets, each starting with a strong action verb, max 25 words
- Quantify outcomes only if numbers exist in the source

PROJECTS:
- Each project: title line, then 1-2 sentence description with key technologies AND outcomes from source
- Never list just a title — always include what it does and what result it achieved

EDUCATION:
- Copy the degree, institution, and year exactly from the source chunk
- Format: "Degree | Institution | Year"
- NEVER write "No education data provided" — if source has education data, use it"""

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

    source_parts = []
    for chunk in selected.get("projects", []):
        source_parts.append(f"[PROJECT] {chunk['content']}")
    for chunk in selected.get("experiences", []):
        source_parts.append(f"[EXPERIENCE] {chunk['content']}")
    for chunk in selected.get("skills", []):
        source_parts.append(f"[SKILLS] {chunk['content']}")
    for chunk in selected.get("education", []):
        source_parts.append(f"[EDUCATION] {chunk['content']}")

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

    text = call_llm(prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3)

    # Normalize: strip trailing colons from standalone section header lines
    # (some LLMs write "SUMMARY:" instead of "SUMMARY")
    _HEADERS = {"SUMMARY", "EXPERIENCE", "PROJECTS", "TECHNICAL SKILLS", "EDUCATION", "SKILLS", "HEADER"}
    normalized = []
    for line in text.split("\n"):
        stripped = line.strip().rstrip(":")
        if stripped.upper() in _HEADERS:
            normalized.append(stripped.upper())
        else:
            normalized.append(line)
    text = "\n".join(normalized)

    return {
        **state,
        "draft_resume": text,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }
