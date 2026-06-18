from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import JobApplication, JobApplicationIn, JobStatusUpdate, JOB_STATUSES
from app.storage.database import get_db
from app.utils.auth_dep import DEFAULT_USER_ID

router = APIRouter()


def _serialize(j: JobApplication) -> dict:
    return {
        "id": j.id,
        "company": j.company,
        "role_title": j.role_title,
        "job_url": j.job_url,
        "jd_text": j.jd_text,
        "resume_version_id": j.resume_version_id,
        "status": j.status,
        "notes": j.notes,
        "applied_at": j.applied_at.isoformat() if j.applied_at else None,
        "created_at": j.created_at.isoformat(),
    }


@router.get("/")
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(JobApplication)
        .where(JobApplication.user_id == DEFAULT_USER_ID)
        .order_by(JobApplication.created_at.desc())
    )
    return [_serialize(j) for j in result.scalars().all()]


@router.post("/", status_code=201)
async def create_job(body: JobApplicationIn, db: AsyncSession = Depends(get_db)):
    if body.status not in JOB_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Choose from: {JOB_STATUSES}")
    job = JobApplication(
        user_id=DEFAULT_USER_ID,
        company=body.company,
        role_title=body.role_title,
        job_url=body.job_url,
        jd_text=body.jd_text,
        resume_version_id=body.resume_version_id,
        status=body.status,
        notes=body.notes,
        applied_at=datetime.utcnow() if body.status == "applied" else None,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return _serialize(job)


@router.patch("/{job_id}")
async def update_job_status(job_id: str, body: JobStatusUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(JobApplication).where(JobApplication.id == job_id, JobApplication.user_id == DEFAULT_USER_ID)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if body.status not in JOB_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Choose from: {JOB_STATUSES}")

    prev_status = job.status
    job.status = body.status
    if body.notes is not None:
        job.notes = body.notes
    if body.resume_version_id is not None:
        job.resume_version_id = body.resume_version_id
    if body.status == "applied" and prev_status != "applied":
        job.applied_at = datetime.utcnow()
    await db.commit()
    await db.refresh(job)
    return _serialize(job)


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(JobApplication).where(JobApplication.id == job_id, JobApplication.user_id == DEFAULT_USER_ID)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.delete(job)
    await db.commit()
