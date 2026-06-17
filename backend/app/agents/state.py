from typing import TypedDict


class ResumeState(TypedDict):
    # Inputs (set at pipeline start)
    job_description: str
    company: str
    role_title: str
    user_id: str

    # Node 1 — JD Analyzer output
    jd_analysis: dict           # {role_type, required_keywords, preferred_keywords, seniority, company_context}

    # Node 2 — Profile Scorer output
    scored_chunks: list[dict]   # [{id, content, metadata, cosine_score, bm25_score, final_score, type, word_count}]

    # Node 3 — Content Selector output
    selected_content: dict      # {projects:[], experiences:[], skills:[], education:[]}
    total_word_count: int

    # Node 4 — Resume Writer output (updated each iteration)
    draft_resume: str
    iteration_count: int

    # Node 5 — ATS Checker output
    ats_score: float
    ats_feedback: list[str]     # missing keywords to weave in on next iteration

    # Node 6 — Report Generator output
    optimization_report: dict   # {match_pct, gap_skills, swappable_items, keyword_coverage}
    resume_version_id: str
