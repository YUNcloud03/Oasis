from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import Certificate, Education, Experience, JobPosting, Project, ResumeVersion, Skill, User, UserProfile
from app.schemas import (
    AiContentResponse,
    ConvertTextRequest,
    OnePageRequest,
    ResumeGenerateRequest,
    ResumeVersionRead,
    StarRewriteRequest,
)
from app.services.ai import complete_text
from app.services.prompts import build_convert_prompt, build_one_page_prompt, build_resume_prompt, build_star_prompt


router = APIRouter(prefix="/resumes", tags=["resumes"])


def _list_names(values: list[str]) -> str:
    return "、".join([value for value in values if value])


def build_profile_snapshot(db: Session, user_id: str) -> dict:
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    educations = list(db.scalars(select(Education).where(Education.user_id == user_id)))
    experiences = list(db.scalars(select(Experience).where(Experience.user_id == user_id)))
    projects = list(db.scalars(select(Project).where(Project.user_id == user_id)))
    skills = list(db.scalars(select(Skill).where(Skill.user_id == user_id)))
    certificates = list(db.scalars(select(Certificate).where(Certificate.user_id == user_id)))

    return {
        "summary": profile.summary if profile else "",
        "target_roles": profile.target_roles if profile else [],
        "target_industries": profile.target_industries if profile else [],
        "education": [
            {
                "name": f"{item.school} {item.department} {item.degree}".strip(),
                "summary": item.description,
            }
            for item in educations
        ],
        "experiences": [
            {
                "name": f"{item.company_name} {item.role}".strip(),
                "summary": "；".join([item.description, _list_names(item.achievements)]).strip("；"),
            }
            for item in experiences
        ],
        "projects": [
            {
                "name": f"{item.project_name} {item.role}".strip(),
                "summary": "；".join([item.description, _list_names(item.technologies), _list_names(item.outcomes)]).strip("；"),
            }
            for item in projects
        ],
        "skills": [
            {"name": item.skill_name, "summary": f"{item.category} / {item.level}"}
            for item in skills
        ],
        "certifications": [
            {"name": item.certificate_name, "summary": item.issuer}
            for item in certificates
        ],
    }


def get_owned_job(db: Session, job_id: str | None, user_id: str) -> JobPosting | None:
    if not job_id:
        return None
    job = db.get(JobPosting, job_id)
    if not job or job.user_id != user_id:
        raise HTTPException(status_code=404, detail="找不到這個職缺。")
    return job


def resolve_target(payload: ResumeGenerateRequest | OnePageRequest, job: JobPosting | None) -> tuple[str, str, str]:
    if not job:
        return payload.target_role, payload.company, payload.jd
    jd = "\n".join(
        [
            job.job_description,
            job.requirements,
            job.preferred_qualifications,
            "、".join(job.culture_traits or []),
        ]
    ).strip()
    return payload.target_role or job.job_title, payload.company or job.company_name, payload.jd or jd


@router.get("", response_model=list[ResumeVersionRead])
def list_resume_versions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ResumeVersion]:
    return list(
        db.scalars(
            select(ResumeVersion)
            .where(ResumeVersion.user_id == current_user.id)
            .order_by(ResumeVersion.created_at.desc())
        )
    )


@router.post("/generate", response_model=AiContentResponse)
def generate_resume(
    payload: ResumeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiContentResponse:
    job = get_owned_job(db, payload.job_id, current_user.id)
    target_role, company, jd = resolve_target(payload, job)
    snapshot = payload.background or build_profile_snapshot(db, current_user.id)
    system, user = build_resume_prompt(
        background=snapshot,
        target_role=target_role,
        company=company,
        jd=jd,
        sections=payload.sections,
        custom_section=payload.custom_section,
        length_overrides=payload.length_overrides,
        supplements=payload.supplements,
        target_style=payload.target_style,
    )
    content = complete_text(system, user, payload.model)

    version = ResumeVersion(
        user_id=current_user.id,
        job_id=job.id if job else None,
        version_type=payload.version_type,
        target_style=payload.target_style,
        generated_content={"content": content, "sections": payload.sections},
        source_snapshot={"background": snapshot, "target_role": target_role, "company": company, "jd": jd},
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return AiContentResponse(content=content, resume_version_id=version.id)


@router.post("/one-page", response_model=AiContentResponse)
def generate_one_page_cv(
    payload: OnePageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiContentResponse:
    job = get_owned_job(db, payload.job_id, current_user.id)
    target_role, company, jd = resolve_target(payload, job)
    snapshot = payload.background or build_profile_snapshot(db, current_user.id)
    system, user = build_one_page_prompt(
        background=snapshot,
        target_role=target_role,
        company=company,
        jd=jd,
        supplements=payload.supplements,
    )
    content = complete_text(system, user, payload.model)

    version = ResumeVersion(
        user_id=current_user.id,
        job_id=job.id if job else None,
        version_type="one-page",
        target_style="concise",
        generated_content={"content": content},
        source_snapshot={"background": snapshot, "target_role": target_role, "company": company, "jd": jd},
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return AiContentResponse(content=content, resume_version_id=version.id)


@router.post("/star", response_model=AiContentResponse)
def rewrite_star(payload: StarRewriteRequest, current_user: User = Depends(get_current_user)) -> AiContentResponse:
    system, user = build_star_prompt(background=payload.original_text, target_role=payload.target_role, jd=payload.jd)
    return AiContentResponse(content=complete_text(system, user, payload.model))


@router.post("/convert", response_model=AiContentResponse)
def convert_text(payload: ConvertTextRequest, current_user: User = Depends(get_current_user)) -> AiContentResponse:
    system, user = build_convert_prompt(payload.text, payload.mode, payload.target_role, payload.jd)
    return AiContentResponse(content=complete_text(system, user, payload.model))
