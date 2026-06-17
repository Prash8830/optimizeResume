import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.database import Base


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    jd_text: Mapped[Optional[str]] = mapped_column(Text)
    company: Mapped[Optional[str]] = mapped_column(String)
    role_title: Mapped[Optional[str]] = mapped_column(String)
    resume_text: Mapped[Optional[str]] = mapped_column(Text)
    ats_score: Mapped[Optional[float]] = mapped_column(Float)
    optimization_report: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Pydantic schemas

class GenerateRequest(BaseModel):
    job_description: str
    company: Optional[str] = ""
    role_title: Optional[str] = ""


class ResumeVersionOut(BaseModel):
    id: str
    company: Optional[str]
    role_title: Optional[str]
    ats_score: Optional[float]
    created_at: datetime
    resume_text: Optional[str]
    optimization_report: Optional[dict]

    class Config:
        from_attributes = True
