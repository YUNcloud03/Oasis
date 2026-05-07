from datetime import datetime, timezone

from app.models import Application, GardenState


APPLICATION_STATUSES = {
    "drafted",
    "applied",
    "interview_invited",
    "interviewing",
    "offer",
    "rejected",
    "ghosted",
    "composted",
}

STATUS_TO_PLANT_STAGE = {
    "drafted": "seed",
    "applied": "seed",
    "interview_invited": "sprout",
    "interviewing": "leaf",
    "offer": "bloom",
    "rejected": "withered",
    "ghosted": "withered",
    "composted": "fertilizer",
}

ALLOWED_TRANSITIONS = {
    "drafted": {"applied", "rejected"},
    "applied": {"interview_invited", "interviewing", "offer", "rejected", "ghosted"},
    "interview_invited": {"interviewing", "offer", "rejected", "ghosted"},
    "interviewing": {"interviewing", "offer", "rejected", "ghosted"},
    "offer": set(),
    "rejected": {"composted"},
    "ghosted": {"composted"},
    "composted": set(),
}


def is_valid_transition(current_status: str, next_status: str) -> bool:
    if current_status == next_status:
        return True
    return next_status in ALLOWED_TRANSITIONS.get(current_status, set())


def bloom_type_for_company(company_type: str) -> str:
    mapping = {
        "finance": "幸運花",
        "tech": "晶亮花",
        "semiconductor": "藍晶花",
        "marketing": "彩瓣花",
        "media": "故事花",
    }
    return mapping.get(company_type.lower(), "OASIS 花")


def sync_garden_state(application: Application, garden_state: GardenState | None = None) -> GardenState:
    state = garden_state or GardenState(application_id=application.id)
    state.plant_stage = STATUS_TO_PLANT_STAGE.get(application.status, "seed")
    state.last_growth_at = datetime.now(timezone.utc)

    if application.status == "offer":
        state.bloom_type = bloom_type_for_company(application.job.company_type)
    if application.status == "composted":
        state.fertilizer_generated = max(state.fertilizer_generated, 5)

    return state
