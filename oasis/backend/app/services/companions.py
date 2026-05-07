from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Companion


SKILL_TO_COMPANION = {
    "python": "tech",
    "sql": "tech",
    "tableau": "analytics",
    "power bi": "analytics",
    "資料分析": "analytics",
    "行銷": "marketing",
    "社群": "marketing",
    "商業分析": "business",
    "策略": "business",
}


def companion_type_for_skill(skill_name: str) -> str | None:
    normalized = skill_name.lower()
    for keyword, companion_type in SKILL_TO_COMPANION.items():
        if keyword in normalized:
            return companion_type
    return None


def unlock_companion_for_skill(db: Session, user_id: str, skill_name: str) -> Companion | None:
    companion_type = companion_type_for_skill(skill_name)
    if not companion_type:
        return None

    existing = db.scalar(
        select(Companion).where(
            Companion.user_id == user_id,
            Companion.companion_type == companion_type,
        )
    )
    if existing:
        existing.level += 1
        return existing

    companion = Companion(
        user_id=user_id,
        companion_type=companion_type,
        unlocked_by_skill=skill_name,
        mood="happy",
    )
    db.add(companion)
    return companion
