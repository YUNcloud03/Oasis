from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def validate_bcrypt_password(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("密碼過長。bcrypt 限制密碼不得超過 72 bytes；若使用中文或特殊符號，請縮短密碼。")
    return value


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_must_fit_bcrypt(cls, value: str) -> str:
        return validate_bcrypt_password(value)


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_must_fit_bcrypt(cls, value: str) -> str:
        return validate_bcrypt_password(value)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    created_at: datetime


class ProfileUpdate(BaseModel):
    summary: str = ""
    target_roles: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    preferred_locale: str = "zh-TW"
    osi_settings: dict = Field(default_factory=dict)


class ProfileRead(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str


class SkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=120)
    category: str = "general"
    level: str = "intermediate"


class SkillRead(SkillCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str


class EducationCreate(BaseModel):
    school: str = Field(min_length=1, max_length=180)
    department: str = ""
    degree: str = ""
    start_date: date | None = None
    end_date: date | None = None
    description: str = ""


class EducationRead(EducationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str


class ExperienceCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=180)
    role: str = Field(min_length=1, max_length=180)
    description: str = ""
    achievements: list[str] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None


class ExperienceRead(ExperienceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str


class ProjectCreate(BaseModel):
    project_name: str = Field(min_length=1, max_length=180)
    role: str = ""
    technologies: list[str] = Field(default_factory=list)
    description: str = ""
    outcomes: list[str] = Field(default_factory=list)


class ProjectRead(ProjectCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str


class CertificateCreate(BaseModel):
    certificate_name: str = Field(min_length=1, max_length=180)
    issuer: str = ""
    issue_date: date | None = None
    expires_at: date | None = None


class CertificateRead(CertificateCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str


class JobCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=180)
    job_title: str = Field(min_length=1, max_length=180)
    job_description: str = Field(min_length=1)
    requirements: str = ""
    preferred_qualifications: str = ""
    company_type: str = ""
    culture_traits: list[str] = Field(default_factory=list)


class JobUpdate(JobCreate):
    pass


class JobRead(JobCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    extracted_keywords: dict
    ideal_candidate_profile: dict
    created_at: datetime
    updated_at: datetime


class ApplicationCreate(BaseModel):
    job_id: str
    resume_version_id: str | None = None
    status: str = "drafted"


class ApplicationStatusUpdate(BaseModel):
    status: str


class GardenStateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    plant_stage: str
    bloom_type: str | None
    fertilizer_generated: int
    last_growth_at: datetime


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    job_id: str
    resume_version_id: str | None
    status: str
    interview_round: int
    applied_at: datetime | None
    created_at: datetime
    updated_at: datetime
    garden_state: GardenStateRead | None = None


class GardenItem(BaseModel):
    application: ApplicationRead
    company_name: str
    job_title: str
    company_type: str


class GardenOverview(BaseModel):
    items: list[GardenItem]
    totals: dict[str, int]


class MatchScoreRequest(BaseModel):
    job_id: str


class JobCompareRequest(BaseModel):
    job_ids: list[str] = Field(min_length=1)


class MatchScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    job_id: str
    overall_score: int
    skill_score: int
    experience_score: int
    education_score: int
    certificate_score: int
    domain_score: int
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    created_at: datetime


class JobCompareItem(BaseModel):
    job_id: str
    company_name: str
    job_title: str
    overall_score: int
    skill_score: int
    experience_score: int
    certificate_score: int
    domain_score: int
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]


class JobCompareResponse(BaseModel):
    recommended_job_id: str | None
    items: list[JobCompareItem]


class CompanionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    companion_type: str
    unlocked_by_skill: str | None
    level: int
    fatigue: int
    mood: str


class FertilizerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    source_application_id: str
    fertilizer_points: int
    generated_reason: str
    ai_review: dict
    created_at: datetime


class ResumeVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    job_id: str | None
    version_type: str
    target_style: str
    generated_content: dict
    source_snapshot: dict
    created_at: datetime
    updated_at: datetime


class ResumeGenerateRequest(BaseModel):
    job_id: str | None = None
    background: dict | None = None
    target_role: str = ""
    company: str = ""
    jd: str = ""
    sections: list[str] = Field(default_factory=lambda: ["自我介紹", "應徵動機", "經歷改寫"])
    custom_section: str = ""
    length_overrides: dict[str, str] = Field(default_factory=dict)
    supplements: list[dict[str, str]] = Field(default_factory=list)
    version_type: str = "custom"
    target_style: str = "formal"
    model: str | None = None


class OnePageRequest(BaseModel):
    job_id: str | None = None
    background: dict | None = None
    target_role: str = ""
    company: str = ""
    jd: str = ""
    supplements: list[dict[str, str]] = Field(default_factory=list)
    model: str | None = None


class StarRewriteRequest(BaseModel):
    original_text: str = Field(min_length=1)
    target_role: str = ""
    jd: str = ""
    model: str | None = None


class ConvertTextRequest(BaseModel):
    text: str = Field(min_length=1)
    mode: str = "rewrite"
    target_role: str = ""
    jd: str = ""
    model: str | None = None


class AiContentResponse(BaseModel):
    content: str
    resume_version_id: str | None = None
