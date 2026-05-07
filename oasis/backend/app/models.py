import uuid
from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


JsonList = MutableList.as_mutable(JSON().with_variant(JSONB, "postgresql"))
JsonDict = MutableDict.as_mutable(JSON().with_variant(JSONB, "postgresql"))


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    profile: Mapped["UserProfile | None"] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    target_roles: Mapped[list[str]] = mapped_column(JsonList, default=list)
    target_industries: Mapped[list[str]] = mapped_column(JsonList, default=list)
    preferred_locale: Mapped[str] = mapped_column(String(16), default="zh-TW")
    osi_settings: Mapped[dict] = mapped_column(JsonDict, default=dict)

    user: Mapped[User] = relationship(back_populates="profile")


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    skill_name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(80), default="general")
    level: Mapped[str] = mapped_column(String(40), default="intermediate")


class Education(Base, TimestampMixin):
    __tablename__ = "educations"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    school: Mapped[str] = mapped_column(String(180), index=True)
    department: Mapped[str] = mapped_column(String(180), default="")
    degree: Mapped[str] = mapped_column(String(120), default="")
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")


class Experience(Base, TimestampMixin):
    __tablename__ = "experiences"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_name: Mapped[str] = mapped_column(String(180), index=True)
    role: Mapped[str] = mapped_column(String(180), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    achievements: Mapped[list[str]] = mapped_column(JsonList, default=list)
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    project_name: Mapped[str] = mapped_column(String(180), index=True)
    role: Mapped[str] = mapped_column(String(180), default="")
    technologies: Mapped[list[str]] = mapped_column(JsonList, default=list)
    description: Mapped[str] = mapped_column(Text, default="")
    outcomes: Mapped[list[str]] = mapped_column(JsonList, default=list)


class Certificate(Base, TimestampMixin):
    __tablename__ = "certificates"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    certificate_name: Mapped[str] = mapped_column(String(180), index=True)
    issuer: Mapped[str] = mapped_column(String(180), default="")
    issue_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(Date, nullable=True)


class JobPosting(Base, TimestampMixin):
    __tablename__ = "job_postings"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_name: Mapped[str] = mapped_column(String(180), index=True)
    job_title: Mapped[str] = mapped_column(String(180), index=True)
    job_description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[str] = mapped_column(Text, default="")
    preferred_qualifications: Mapped[str] = mapped_column(Text, default="")
    company_type: Mapped[str] = mapped_column(String(120), default="")
    culture_traits: Mapped[list[str]] = mapped_column(JsonList, default=list)
    extracted_keywords: Mapped[dict] = mapped_column(JsonDict, default=dict)
    ideal_candidate_profile: Mapped[dict] = mapped_column(JsonDict, default=dict)


class ResumeVersion(Base, TimestampMixin):
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True)
    version_type: Mapped[str] = mapped_column(String(60), default="data")
    target_style: Mapped[str] = mapped_column(String(60), default="formal")
    generated_content: Mapped[dict] = mapped_column(JsonDict, default=dict)
    source_snapshot: Mapped[dict] = mapped_column(JsonDict, default=dict)


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"), index=True)
    resume_version_id: Mapped[str | None] = mapped_column(ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="drafted", index=True)
    interview_round: Mapped[int] = mapped_column(Integer, default=0)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job: Mapped[JobPosting] = relationship()
    garden_state: Mapped["GardenState | None"] = relationship(back_populates="application", cascade="all, delete-orphan")


class MatchScore(Base, TimestampMixin):
    __tablename__ = "match_scores"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"), index=True)
    overall_score: Mapped[int] = mapped_column(Integer)
    skill_score: Mapped[int] = mapped_column(Integer)
    experience_score: Mapped[int] = mapped_column(Integer)
    education_score: Mapped[int] = mapped_column(Integer)
    certificate_score: Mapped[int] = mapped_column(Integer)
    domain_score: Mapped[int] = mapped_column(Integer)
    strengths: Mapped[list[str]] = mapped_column(JsonList, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JsonList, default=list)
    suggestions: Mapped[list[str]] = mapped_column(JsonList, default=list)


class GardenState(Base, TimestampMixin):
    __tablename__ = "garden_states"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), unique=True, index=True)
    plant_stage: Mapped[str] = mapped_column(String(40), default="seed")
    bloom_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    fertilizer_generated: Mapped[int] = mapped_column(Integer, default=0)
    last_growth_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped[Application] = relationship(back_populates="garden_state")


class Companion(Base, TimestampMixin):
    __tablename__ = "companions"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    companion_type: Mapped[str] = mapped_column(String(60), index=True)
    unlocked_by_skill: Mapped[str | None] = mapped_column(String(120), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    fatigue: Mapped[int] = mapped_column(Integer, default=0)
    mood: Mapped[str] = mapped_column(String(40), default="focused")


class FertilizerLog(Base, TimestampMixin):
    __tablename__ = "fertilizer_logs"

    id: Mapped[str] = mapped_column(String(36).with_variant(UUID(as_uuid=False), "postgresql"), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_application_id: Mapped[str] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    fertilizer_points: Mapped[int] = mapped_column(Integer)
    generated_reason: Mapped[str] = mapped_column(Text)
    ai_review: Mapped[dict] = mapped_column(JsonDict, default=dict)
