import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import ResumeState
from app.models.resume import ResumeVersion
from app.storage.database import AsyncSessionLocal


async def report_generator(state: ResumeState) -> ResumeState:
    jd = state["jd_analysis"]
    required_kws = set(jd.get("required_keywords", {}).keys())
    preferred_kws = set(jd.get("preferred_keywords", {}).keys())
    resume_lower = state["draft_resume"].lower()

    # Keyword coverage analysis
    matched_required = [kw for kw in required_kws if kw.lower() in resume_lower]
    missing_required = [kw for kw in required_kws if kw.lower() not in resume_lower]
    matched_preferred = [kw for kw in preferred_kws if kw.lower() in resume_lower]
    missing_preferred = [kw for kw in preferred_kws if kw.lower() not in resume_lower]

    # Chunks that scored well but didn't make it in (space constraint)
    selected_ids = set()
    for chunks in state["selected_content"].values():
        for chunk in chunks:
            selected_ids.add(chunk.get("id", ""))

    swappable = [
        {"content": c["content"][:100], "score": c["final_score"]}
        for c in state["scored_chunks"]
        if c.get("id") not in selected_ids and c["final_score"] >= 0.40
    ][:5]

    # Gap skills — required keywords with no corresponding profile chunk
    all_profile_text = " ".join(c["content"] for c in state["scored_chunks"]).lower()
    gap_skills = [kw for kw in required_kws if kw.lower() not in all_profile_text]

    optimization_report = {
        "match_percentage": round(state["ats_score"] * 100, 1),
        "iteration_count": state.get("iteration_count", 1),
        "word_count": state.get("total_word_count", 0),
        "required_keyword_coverage": {
            "matched": matched_required,
            "missing": missing_required,
        },
        "preferred_keyword_coverage": {
            "matched": matched_preferred,
            "missing": missing_preferred,
        },
        "gap_skills": gap_skills,
        "swappable_items": swappable,
    }

    # Persist to PostgreSQL
    resume_version_id = ""
    try:
        async with AsyncSessionLocal() as db:
            version = ResumeVersion(
                user_id=state["user_id"],
                jd_text=state["job_description"],
                company=state["company"],
                role_title=state["role_title"],
                resume_text=state["draft_resume"],
                ats_score=state["ats_score"],
                optimization_report=optimization_report,
            )
            db.add(version)
            await db.commit()
            await db.refresh(version)
            resume_version_id = version.id
    except Exception as e:
        print(f"[report_gen] DB save failed: {e}")

    return {
        **state,
        "optimization_report": optimization_report,
        "resume_version_id": resume_version_id,
    }
