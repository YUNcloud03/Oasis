from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import JobPosting, User
from app.schemas import JobCreate, JobRead, JobUpdate
from app.services.jobs import build_ideal_candidate_profile, extract_job_keywords


router = APIRouter(prefix="/jobs", tags=["jobs"])


def enrich_job(job: JobPosting) -> None:
    text = " ".join(
        [
            job.job_title,
            job.job_description,
            job.requirements,
            job.preferred_qualifications,
            job.company_type,
            " ".join(job.culture_traits or []),
        ]
    )
    keywords = extract_job_keywords(text)
    job.extracted_keywords = keywords
    job.ideal_candidate_profile = build_ideal_candidate_profile(keywords)


@router.get("", response_model=list[JobRead])
def list_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[JobPosting]:
    return list(
        db.scalars(select(JobPosting).where(JobPosting.user_id == current_user.id).order_by(JobPosting.created_at.desc()))
    )


@router.post("", response_model=JobRead, status_code=201)
def create_job(
    payload: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobPosting:
    job = JobPosting(user_id=current_user.id, **payload.model_dump())
    enrich_job(job)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> JobPosting:
    job = db.get(JobPosting, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="找不到職缺。")
    return job


@router.put("/{job_id}", response_model=JobRead)
def update_job(
    job_id: str,
    payload: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobPosting:
    job = db.get(JobPosting, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="找不到職缺。")
    for key, value in payload.model_dump().items():
        setattr(job, key, value)
    enrich_job(job)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    job = db.get(JobPosting, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="找不到職缺。")
    db.delete(job)
    db.commit()


@router.post("/{job_id}/analyze", response_model=JobRead)
def analyze_job(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> JobPosting:
    job = db.get(JobPosting, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="找不到職缺。")
    enrich_job(job)
    db.commit()
    db.refresh(job)
    return job
