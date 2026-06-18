import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.database import Base

JOB_STATUSES = ("bookmarked", "applied", "interview", "offer", "rejected")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False)
    role_title: Mapped[str] = mapped_column(String, nullable=False)
    job_url: Mapped[Optional[str]] = mapped_column(String)
    jd_text: Mapped[Optional[str]] = mapped_column(Text)
    resume_version_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("resume_versions.id"))
    status: Mapped[str] = mapped_column(String, default="bookmarked")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class JobApplicationIn(BaseModel):
    company: str
    role_title: str
    job_url: Optional[str] = None
    jd_text: Optional[str] = None
    resume_version_id: Optional[str] = None
    status: str = "bookmarked"
    notes: Optional[str] = None


class JobStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    resume_version_id: Optional[str] = None
