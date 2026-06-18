import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import (
    Education, EducationIn, Experience, ExperienceIn,
    MasterProfile, ProfileIn, Project, ProjectIn, Skill, SkillIn,
)
from app.storage.database import get_db
from app.storage.vector_store import index_user_profile
from app.utils.auth_dep import DEFAULT_USER_ID
from app.utils.llm import call_llm

router = APIRouter()

# ── AI Profile Consultant chat ─────────────────────────────────────────────

PROFILE_SYSTEM_PROMPT = """You are an expert career consultant building a user's master resume profile.
Be warm, concise, and probe for specifics (numbers, outcomes, tech stacks).
Ask ONE focused question at a time. Cover: basic info, work experience, projects, skills, education.
After all sections are covered, say exactly: PROFILE_COMPLETE — then stop asking questions."""


class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    resume_context: str = ""


class ChatResponse(BaseModel):
    reply: str
    profile_complete: bool


class ExtractRequest(BaseModel):
    messages: list[ChatMessage]


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    system = PROFILE_SYSTEM_PROMPT
    if body.resume_context:
        system += f"\n\nRESUME CONTEXT:\n{body.resume_context[:3000]}"

    msgs: list[dict] = []
    if system:
        msgs.append({"role": "system", "content": system})
    for m in body.messages:
        msgs.append({"role": m.role, "content": m.content})

    # If no messages yet, just get opening message
    if not body.messages:
        msgs.append({"role": "user", "content": "Hello, I'd like to build my resume profile."})

    reply = call_llm("", system_prompt="", temperature=0.7, endpoint="profile_chat",
                     _messages_override=msgs)
    return ChatResponse(reply=reply, profile_complete="PROFILE_COMPLETE" in reply)


@router.post("/extract")
async def extract_profile(body: ExtractRequest):
    conversation = "\n".join(
        f"{'User' if m.role == 'user' else 'Consultant'}: {m.content}"
        for m in body.messages
    )
    prompt = f"""Extract a structured JSON profile from this conversation.
Return ONLY valid JSON with these keys: name, email, phone, linkedin, github, summary, projects (array with title/description/tech_stack/outcomes/github_url), skills (array with name/category/proficiency), experiences (array with company/role/start_date/end_date/bullets), education (array with degree/institution/year).

Conversation:
{conversation}"""
    result = call_llm(prompt, temperature=0.1, json_mode=True, endpoint="profile_extract")
    try:
        return json.loads(result)
    except Exception:
        return {}


@router.get("/")
async def get_profile(db: AsyncSession = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    result = await db.execute(select(MasterProfile).where(MasterProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    projects = (await db.execute(select(Project).where(Project.profile_id == profile.id))).scalars().all()
    skills = (await db.execute(select(Skill).where(Skill.profile_id == profile.id))).scalars().all()
    experiences = (await db.execute(select(Experience).where(Experience.profile_id == profile.id))).scalars().all()
    education = (await db.execute(select(Education).where(Education.profile_id == profile.id))).scalars().all()

    return {
        "profile": profile,
        "projects": projects,
        "skills": skills,
        "experiences": experiences,
        "education": education,
    }


@router.post("/", status_code=201)
async def save_profile(body: ProfileIn, db: AsyncSession = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    # Upsert master profile
    result = await db.execute(select(MasterProfile).where(MasterProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        profile = MasterProfile(user_id=user_id)
        db.add(profile)

    profile.name = body.name
    profile.email = body.email
    profile.phone = body.phone
    profile.linkedin = body.linkedin
    profile.github = body.github
    profile.summary = body.summary
    await db.flush()

    # Replace all sub-items
    for model_cls in [Project, Skill, Experience, Education]:
        existing = (await db.execute(select(model_cls).where(model_cls.profile_id == profile.id))).scalars().all()
        for item in existing:
            await db.delete(item)

    for p in body.projects:
        words = len((p.description or "").split()) + len(" ".join(p.tech_stack).split()) + len(" ".join(p.outcomes).split())
        db.add(Project(profile_id=profile.id, word_count=words, **p.model_dump()))

    for s in body.skills:
        db.add(Skill(profile_id=profile.id, **s.model_dump()))

    for e in body.experiences:
        db.add(Experience(profile_id=profile.id, **e.model_dump()))

    for ed in body.education:
        db.add(Education(profile_id=profile.id, **ed.model_dump()))

    await db.commit()

    # Trigger async embedding
    await index_user_profile(user_id, body)

    return {"message": "Profile saved and indexed", "profile_id": profile.id}


@router.get("/form-data")
async def get_form_data(db: AsyncSession = Depends(get_db)):
    """Flat key-value profile optimised for auto-filling job application forms."""
    user_id = DEFAULT_USER_ID
    result = await db.execute(select(MasterProfile).where(MasterProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    experiences = (await db.execute(select(Experience).where(Experience.profile_id == profile.id))).scalars().all()
    education_list = (await db.execute(select(Education).where(Education.profile_id == profile.id))).scalars().all()

    current_exp = experiences[0] if experiences else None
    current_edu = education_list[0] if education_list else None

    return {
        "full_name": profile.name or "",
        "first_name": (profile.name or "").split()[0],
        "last_name": " ".join((profile.name or "").split()[1:]),
        "email": profile.email or "",
        "phone": profile.phone or "",
        "linkedin": profile.linkedin or "",
        "github": profile.github or "",
        "current_company": current_exp.company if current_exp else "",
        "current_role": current_exp.role if current_exp else "",
        "current_start_date": current_exp.start_date if current_exp else "",
        "degree": current_edu.degree if current_edu else "",
        "institution": current_edu.institution if current_edu else "",
        "graduation_year": current_edu.year if current_edu else "",
        "summary": profile.summary or "",
        "years_experience": "2",
    }


@router.post("/index")
async def reindex_profile(db: AsyncSession = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    """Re-embed the entire profile into ChromaDB (use after bulk edits)."""
    result = await db.execute(select(MasterProfile).where(MasterProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    projects = (await db.execute(select(Project).where(Project.profile_id == profile.id))).scalars().all()
    skills = (await db.execute(select(Skill).where(Skill.profile_id == profile.id))).scalars().all()
    experiences = (await db.execute(select(Experience).where(Experience.profile_id == profile.id))).scalars().all()

    from app.models.profile import ProfileIn, ProjectIn, SkillIn, ExperienceIn
    profile_data = ProfileIn(
        name=profile.name or "",
        email=profile.email or "",
        projects=[ProjectIn(**{k: getattr(p, k) for k in ProjectIn.model_fields}) for p in projects],
        skills=[SkillIn(**{k: getattr(s, k) for k in SkillIn.model_fields}) for s in skills],
        experiences=[ExperienceIn(**{k: getattr(e, k) for k in ExperienceIn.model_fields}) for e in experiences],
    )
    await index_user_profile(user_id, profile_data)
    return {"message": "Profile re-indexed successfully"}
