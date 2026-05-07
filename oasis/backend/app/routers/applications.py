from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.deps import get_current_user
from app.models import Application, GardenState, JobPosting, User
from app.schemas import ApplicationCreate, ApplicationRead, ApplicationStatusUpdate
from app.services.garden import APPLICATION_STATUSES, is_valid_transition, sync_garden_state


router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Application]:
    statement = (
        select(Application)
        .options(selectinload(Application.garden_state))
        .where(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc())
    )
    return list(db.scalars(statement))


@router.post("", response_model=ApplicationRead, status_code=201)
def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Application:
    job = db.get(JobPosting, payload.job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="找不到職缺。")
    if payload.status not in APPLICATION_STATUSES:
        raise HTTPException(status_code=400, detail="不支援的投遞狀態。")

    application = Application(
        user_id=current_user.id,
        job_id=payload.job_id,
        resume_version_id=payload.resume_version_id,
        status=payload.status,
        applied_at=datetime.now(timezone.utc) if payload.status == "applied" else None,
    )
    db.add(application)
    db.flush()
    garden_state = sync_garden_state(application)
    db.add(garden_state)
    db.commit()
    db.refresh(application)
    return application


@router.patch("/{application_id}/status", response_model=ApplicationRead)
def update_application_status(
    application_id: str,
    payload: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Application:
    application = db.scalar(
        select(Application)
        .options(selectinload(Application.garden_state), selectinload(Application.job))
        .where(Application.id == application_id)
    )
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="找不到投遞紀錄。")
    if payload.status not in APPLICATION_STATUSES:
        raise HTTPException(status_code=400, detail="不支援的投遞狀態。")
    if not is_valid_transition(application.status, payload.status):
        raise HTTPException(status_code=400, detail="此狀態轉換不符合花園規則。")

    application.status = payload.status
    if payload.status == "applied" and not application.applied_at:
        application.applied_at = datetime.now(timezone.utc)
    if payload.status in {"interview_invited", "interviewing"}:
        application.interview_round = max(1, application.interview_round + 1)

    garden_state = sync_garden_state(application, application.garden_state)
    if not application.garden_state:
        db.add(garden_state)

    db.commit()
    db.refresh(application)
    return application
