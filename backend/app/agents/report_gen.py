import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import ResumeState
from app.models.profile import Education, MasterProfile
from app.models.resume import ResumeVersion
from app.storage.database import AsyncSessionLocal


async def _build_contact_header(user_id: str) -> str:
    """Fetch profile from DB and build a HEADER block to prepend to resume text."""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(MasterProfile).where(MasterProfile.user_id == user_id))
            profile = result.scalar_one_or_none()
        if not profile:
            return ""
        contact_parts = [p for p in [profile.email, profile.phone, profile.linkedin, profile.github] if p]
        name = profile.name or ""
        contact_line = " | ".join(contact_parts)
        return f"HEADER\n{name}\n{contact_line}\n\n"
    except Exception:
        return ""


async def _build_education_section(user_id: str) -> str:
    """Fetch education from DB and build EDUCATION section if not already in resume."""
    try:
        async with AsyncSessionLocal() as db:
            prof_result = await db.execute(select(MasterProfile).where(MasterProfile.user_id == user_id))
            profile = prof_result.scalar_one_or_none()
            if not profile:
                return ""
            edu_result = await db.execute(select(Education).where(Education.profile_id == profile.id))
            educations = edu_result.scalars().all()
        if not educations:
            return ""
        lines = ["EDUCATION"]
        for edu in educations:
            parts = [p for p in [edu.degree, edu.institution, edu.year] if p]
            lines.append(" | ".join(parts))
        return "\n" + "\n".join(lines) + "\n"
    except Exception:
        return ""


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

    # Prepend contact header and fix education section
    contact_header = await _build_contact_header(state["user_id"])
    draft = state["draft_resume"]

    edu_lines = [l.strip() for l in draft.split("\n")]
    has_edu_header = any(l.upper() == "EDUCATION" for l in edu_lines)

    # Detect LLM filler: header present but content is empty or placeholder
    edu_header_idx = next((i for i, l in enumerate(edu_lines) if l.upper() == "EDUCATION"), -1)
    edu_content_after = " ".join(edu_lines[edu_header_idx + 1:edu_header_idx + 4]).lower() if edu_header_idx >= 0 else ""
    edu_is_filler = not edu_content_after.strip() or any(
        phrase in edu_content_after for phrase in ["no education", "not provided", "n/a", "none"]
    )

    if not has_edu_header:
        # Section missing entirely — append from DB
        education_section = await _build_education_section(state["user_id"])
        full_resume_text = contact_header + draft + education_section
    elif edu_is_filler:
        # LLM wrote filler — strip it and replace with DB data
        real_edu = await _build_education_section(state["user_id"])
        lines = draft.split("\n")
        edu_line_idx = next((i for i, l in enumerate(lines) if l.strip().upper() == "EDUCATION"), -1)
        draft_without_edu = "\n".join(lines[:edu_line_idx]).rstrip()
        full_resume_text = contact_header + draft_without_edu + real_edu
    else:
        full_resume_text = contact_header + draft

    # Persist to PostgreSQL
    resume_version_id = ""
    try:
        async with AsyncSessionLocal() as db:
            version = ResumeVersion(
                user_id=state["user_id"],
                jd_text=state["job_description"],
                company=state["company"],
                role_title=state["role_title"],
                resume_text=full_resume_text,
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
