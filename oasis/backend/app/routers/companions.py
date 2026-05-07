from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import Companion, User
from app.schemas import CompanionRead


router = APIRouter(prefix="/companions", tags=["companions"])


@router.get("", response_model=list[CompanionRead])
def list_companions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Companion]:
    return list(
        db.scalars(
            select(Companion).where(Companion.user_id == current_user.id).order_by(Companion.created_at.desc())
        )
    )
