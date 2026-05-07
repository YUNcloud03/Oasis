from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.deps import get_current_user
from app.models import Application, User
from app.schemas import GardenItem, GardenOverview


router = APIRouter(prefix="/garden", tags=["garden"])


@router.get("", response_model=GardenOverview)
def garden_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> GardenOverview:
    applications = list(
        db.scalars(
            select(Application)
            .options(selectinload(Application.job), selectinload(Application.garden_state))
            .where(Application.user_id == current_user.id)
            .order_by(Application.created_at.desc())
        )
    )

    totals = {
        "applied": 0,
        "interviewing": 0,
        "offer": 0,
        "withered": 0,
        "fertilizer_points": 0,
    }
    items: list[GardenItem] = []

    for application in applications:
        if application.status == "applied":
            totals["applied"] += 1
        if application.status in {"interview_invited", "interviewing"}:
            totals["interviewing"] += 1
        if application.status == "offer":
            totals["offer"] += 1
        if application.status in {"rejected", "ghosted", "composted"}:
            totals["withered"] += 1
        if application.garden_state:
            totals["fertilizer_points"] += application.garden_state.fertilizer_generated

        items.append(
            GardenItem(
                application=application,
                company_name=application.job.company_name,
                job_title=application.job.job_title,
                company_type=application.job.company_type,
            )
        )

    return GardenOverview(items=items, totals=totals)
