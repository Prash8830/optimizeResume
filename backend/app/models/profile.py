import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.database import Base


# SQLAlchemy ORM models

class MasterProfile(Base):
    __tablename__ = "master_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String)
    phone: Mapped[Optional[str]] = mapped_column(String)
    linkedin: Mapped[Optional[str]] = mapped_column(String)
    github: Mapped[Optional[str]] = mapped_column(String)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("master_profiles.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    tech_stack: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    outcomes: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    role_types: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    duration: Mapped[Optional[str]] = mapped_column(String)
    github_url: Mapped[Optional[str]] = mapped_column(String)
    word_count: Mapped[Optional[int]] = mapped_column(default=0)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("master_profiles.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String)
    domain: Mapped[Optional[str]] = mapped_column(String)
    proficiency: Mapped[Optional[str]] = mapped_column(String)


class Experience(Base):
    __tablename__ = "experiences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("master_profiles.id"), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String)
    role: Mapped[Optional[str]] = mapped_column(String)
    start_date: Mapped[Optional[str]] = mapped_column(String)
    end_date: Mapped[Optional[str]] = mapped_column(String)
    bullets: Mapped[Optional[list]] = mapped_column(ARRAY(String))


class Education(Base):
    __tablename__ = "education"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("master_profiles.id"), nullable=False)
    degree: Mapped[Optional[str]] = mapped_column(String)
    institution: Mapped[Optional[str]] = mapped_column(String)
    year: Mapped[Optional[str]] = mapped_column(String)
    relevant_coursework: Mapped[Optional[list]] = mapped_column(ARRAY(String))


# Pydantic schemas

class ProjectIn(BaseModel):
    title: str
    description: Optional[str] = None
    tech_stack: list[str] = []
    outcomes: list[str] = []
    role_types: list[str] = []
    duration: Optional[str] = None
    github_url: Optional[str] = None


class SkillIn(BaseModel):
    name: str
    category: Optional[str] = None
    domain: Optional[str] = None
    proficiency: Optional[str] = "proficient"


class ExperienceIn(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: Optional[str] = "Present"
    bullets: list[str] = []


class EducationIn(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None
    relevant_coursework: list[str] = []


class ProfileIn(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None
    projects: list[ProjectIn] = []
    skills: list[SkillIn] = []
    experiences: list[ExperienceIn] = []
    education: list[EducationIn] = []
