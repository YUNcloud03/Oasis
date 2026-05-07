from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.deps import get_current_user
from app.models import Application, FertilizerLog, User
from app.schemas import FertilizerRead
from app.services.garden import sync_garden_state


router = APIRouter(prefix="/fertilizer", tags=["fertilizer"])


@router.get("", response_model=list[FertilizerRead])
def list_fertilizer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FertilizerLog]:
    return list(
        db.scalars(
            select(FertilizerLog)
            .where(FertilizerLog.user_id == current_user.id)
            .order_by(FertilizerLog.created_at.desc())
        )
    )


@router.post("/convert/{application_id}", response_model=FertilizerRead)
def convert_to_fertilizer(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FertilizerLog:
    application = db.scalar(
        select(Application)
        .options(selectinload(Application.job), selectinload(Application.garden_state))
        .where(Application.id == application_id)
    )
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="找不到投遞紀錄。")
    if application.status not in {"rejected", "ghosted", "composted"}:
        raise HTTPException(status_code=400, detail="只有未錄取或無聲卡可轉化為經驗化肥。")

    application.status = "composted"
    garden_state = sync_garden_state(application, application.garden_state)
    if not application.garden_state:
        db.add(garden_state)

    log = FertilizerLog(
        user_id=current_user.id,
        source_application_id=application.id,
        fertilizer_points=garden_state.fertilizer_generated,
        generated_reason="將未錄取或無聲卡經驗轉化為下一次優化履歷的養分。",
        ai_review={
            "possible_reasons": ["履歷關鍵字可能未完全對齊 JD。"],
            "resume_fixes": ["補上量化成果與職缺必要技能。"],
            "encouragement": "每一次經驗都是 Osi 花園的養分。",
        },
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
