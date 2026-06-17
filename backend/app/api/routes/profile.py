from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import (
    Education, EducationIn, Experience, ExperienceIn,
    MasterProfile, ProfileIn, Project, ProjectIn, Skill, SkillIn,
)
from app.storage.database import get_db
from app.storage.vector_store import index_user_profile
from app.utils.auth_dep import get_current_user_id

router = APIRouter()


@router.get("/")
async def get_profile(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
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
async def save_profile(
    body: ProfileIn,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
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


@router.post("/index")
async def reindex_profile(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
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
