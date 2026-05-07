from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import Certificate, Education, Experience, Project, Skill, User, UserProfile
from app.schemas import (
    CertificateCreate,
    CertificateRead,
    EducationCreate,
    EducationRead,
    ExperienceCreate,
    ExperienceRead,
    ProfileRead,
    ProfileUpdate,
    ProjectCreate,
    ProjectRead,
    SkillCreate,
    SkillRead,
)
from app.services.companions import unlock_companion_for_skill


router = APIRouter(tags=["profile"])


def get_owned_or_404(db: Session, model: type, item_id: str, user_id: str):
    item = db.get(model, item_id)
    if not item or item.user_id != user_id:
        raise HTTPException(status_code=404, detail="找不到資料。")
    return item


@router.get("/profile", response_model=ProfileRead)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserProfile:
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))
    if not profile:
        profile = UserProfile(user_id=current_user.id, preferred_locale="zh-TW")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("/profile", response_model=ProfileRead)
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/skills", response_model=list[SkillRead])
def list_skills(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Skill]:
    return list(db.scalars(select(Skill).where(Skill.user_id == current_user.id).order_by(Skill.created_at.desc())))


@router.post("/skills", response_model=SkillRead, status_code=201)
def create_skill(
    payload: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Skill:
    skill = Skill(user_id=current_user.id, **payload.model_dump())
    db.add(skill)
    unlock_companion_for_skill(db, current_user.id, skill.skill_name)
    db.commit()
    db.refresh(skill)
    return skill


@router.put("/skills/{skill_id}", response_model=SkillRead)
def update_skill(
    skill_id: str,
    payload: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Skill:
    skill = db.get(Skill, skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="找不到技能。")
    for key, value in payload.model_dump().items():
        setattr(skill, key, value)
    unlock_companion_for_skill(db, current_user.id, skill.skill_name)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/skills/{skill_id}", status_code=204)
def delete_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    skill = db.get(Skill, skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="找不到技能。")
    db.delete(skill)
    db.commit()


@router.get("/educations", response_model=list[EducationRead])
def list_educations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Education]:
    return list(
        db.scalars(select(Education).where(Education.user_id == current_user.id).order_by(Education.created_at.desc()))
    )


@router.post("/educations", response_model=EducationRead, status_code=201)
def create_education(
    payload: EducationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Education:
    education = Education(user_id=current_user.id, **payload.model_dump())
    db.add(education)
    db.commit()
    db.refresh(education)
    return education


@router.put("/educations/{education_id}", response_model=EducationRead)
def update_education(
    education_id: str,
    payload: EducationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Education:
    education = get_owned_or_404(db, Education, education_id, current_user.id)
    for key, value in payload.model_dump().items():
        setattr(education, key, value)
    db.commit()
    db.refresh(education)
    return education


@router.delete("/educations/{education_id}", status_code=204)
def delete_education(
    education_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    education = get_owned_or_404(db, Education, education_id, current_user.id)
    db.delete(education)
    db.commit()


@router.get("/experiences", response_model=list[ExperienceRead])
def list_experiences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Experience]:
    return list(
        db.scalars(select(Experience).where(Experience.user_id == current_user.id).order_by(Experience.created_at.desc()))
    )


@router.post("/experiences", response_model=ExperienceRead, status_code=201)
def create_experience(
    payload: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Experience:
    experience = Experience(user_id=current_user.id, **payload.model_dump())
    db.add(experience)
    db.commit()
    db.refresh(experience)
    return experience


@router.put("/experiences/{experience_id}", response_model=ExperienceRead)
def update_experience(
    experience_id: str,
    payload: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Experience:
    experience = get_owned_or_404(db, Experience, experience_id, current_user.id)
    for key, value in payload.model_dump().items():
        setattr(experience, key, value)
    db.commit()
    db.refresh(experience)
    return experience


@router.delete("/experiences/{experience_id}", status_code=204)
def delete_experience(
    experience_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    experience = get_owned_or_404(db, Experience, experience_id, current_user.id)
    db.delete(experience)
    db.commit()


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Project]:
    return list(
        db.scalars(select(Project).where(Project.user_id == current_user.id).order_by(Project.created_at.desc()))
    )


@router.post("/projects", response_model=ProjectRead, status_code=201)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = Project(user_id=current_user.id, **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.put("/projects/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = get_owned_or_404(db, Project, project_id, current_user.id)
    for key, value in payload.model_dump().items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    project = get_owned_or_404(db, Project, project_id, current_user.id)
    db.delete(project)
    db.commit()


@router.get("/certificates", response_model=list[CertificateRead])
def list_certificates(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Certificate]:
    return list(
        db.scalars(
            select(Certificate).where(Certificate.user_id == current_user.id).order_by(Certificate.created_at.desc())
        )
    )


@router.post("/certificates", response_model=CertificateRead, status_code=201)
def create_certificate(
    payload: CertificateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Certificate:
    certificate = Certificate(user_id=current_user.id, **payload.model_dump())
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return certificate


@router.put("/certificates/{certificate_id}", response_model=CertificateRead)
def update_certificate(
    certificate_id: str,
    payload: CertificateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Certificate:
    certificate = get_owned_or_404(db, Certificate, certificate_id, current_user.id)
    for key, value in payload.model_dump().items():
        setattr(certificate, key, value)
    db.commit()
    db.refresh(certificate)
    return certificate


@router.delete("/certificates/{certificate_id}", status_code=204)
def delete_certificate(
    certificate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    certificate = get_owned_or_404(db, Certificate, certificate_id, current_user.id)
    db.delete(certificate)
    db.commit()
