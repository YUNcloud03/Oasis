from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import JobPosting, MatchScore, Skill, User, UserProfile
from app.schemas import JobCompareItem, JobCompareRequest, JobCompareResponse, MatchScoreRead, MatchScoreRequest
from app.services.match import calculate_match_score


router = APIRouter(prefix="/match", tags=["match"])


@router.post("/score", response_model=MatchScoreRead)
def score_job(
    payload: MatchScoreRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchScore:
    job = db.get(JobPosting, payload.job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="找不到職缺。")

    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))
    skills = list(db.scalars(select(Skill).where(Skill.user_id == current_user.id)))
    result = calculate_match_score(profile, skills, job)

    score = MatchScore(user_id=current_user.id, job_id=job.id, **result)
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


@router.post("/compare", response_model=JobCompareResponse)
def compare_jobs(
    payload: JobCompareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobCompareResponse:
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))
    skills = list(db.scalars(select(Skill).where(Skill.user_id == current_user.id)))

    jobs = list(
        db.scalars(
            select(JobPosting).where(
                JobPosting.user_id == current_user.id,
                JobPosting.id.in_(payload.job_ids),
            )
        )
    )
    found_ids = {job.id for job in jobs}
    missing_ids = set(payload.job_ids) - found_ids
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"找不到職缺：{', '.join(sorted(missing_ids))}")

    items: list[JobCompareItem] = []
    for job in jobs:
        result = calculate_match_score(profile, skills, job)
        items.append(
            JobCompareItem(
                job_id=job.id,
                company_name=job.company_name,
                job_title=job.job_title,
                overall_score=result["overall_score"],
                skill_score=result["skill_score"],
                experience_score=result["experience_score"],
                certificate_score=result["certificate_score"],
                domain_score=result["domain_score"],
                strengths=result["strengths"],
                weaknesses=result["weaknesses"],
                suggestions=result["suggestions"],
            )
        )

    items.sort(key=lambda item: item.overall_score, reverse=True)
    return JobCompareResponse(
        recommended_job_id=items[0].job_id if items else None,
        items=items,
    )
