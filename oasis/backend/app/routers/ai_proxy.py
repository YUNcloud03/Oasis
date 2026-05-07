from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.ai import complete_text
from app.services.prompts import (
    build_convert_rewrite_prompt,
    build_convert_translate_prompt,
    build_match_prompt,
    build_one_page_prompt,
    build_resume_prompt,
    build_star_prompt,
)


router = APIRouter(prefix="/api", tags=["ai-proxy"])
settings = get_settings()

BackgroundType = dict[str, list[dict[str, str]]] | str


def require_app_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.app_token:
        raise HTTPException(status_code=401, detail="Invalid APP_TOKEN")
    return token


class AiBase(BaseModel):
    model: str | None = None


class ResumeReq(AiBase):
    background: BackgroundType = Field(default_factory=dict)
    target_role: str = ""
    company: str = ""
    jd: str = ""
    sections: list[str] = Field(default_factory=list)
    custom_section: str = ""
    length_overrides: dict[str, str] = Field(default_factory=dict)
    supplements: list[dict[str, str]] = Field(default_factory=list)


class MatchReq(AiBase):
    background: BackgroundType = Field(default_factory=dict)
    target_role: str = ""
    company: str = ""
    jd: str


class OnePageReq(AiBase):
    background: BackgroundType = Field(default_factory=dict)
    target_role: str = ""
    company: str = ""
    jd: str = ""
    supplements: list[dict[str, str]] = Field(default_factory=list)


class StarReq(AiBase):
    background: BackgroundType = Field(default_factory=dict)
    target_role: str = ""
    jd: str = ""


class ConvertReq(AiBase):
    mode: str
    original_resume: str = Field(min_length=1)
    background: BackgroundType = Field(default_factory=dict)
    from_domain: str = ""
    to_domain: str = ""
    target_jd: str = ""


def _background_is_empty(background: BackgroundType) -> bool:
    if isinstance(background, str):
        return not background.strip()
    return not any(
        (item.get("name") or "").strip()
        for items in background.values()
        for item in (items or [])
        if isinstance(item, dict)
    )


@router.get("/health")
def proxy_health() -> dict:
    return {"ok": True, "model": settings.openai_model, "auth": "app-token"}


@router.post("/resume/generate")
def resume_generate(payload: ResumeReq, _token: str = Depends(require_app_token)) -> dict[str, str]:
    if not payload.sections:
        raise HTTPException(status_code=400, detail="請至少選擇一個履歷區塊。")
    system, user = build_resume_prompt(
        background=payload.background,
        target_role=payload.target_role,
        company=payload.company,
        jd=payload.jd,
        sections=payload.sections,
        custom_section=payload.custom_section,
        length_overrides=payload.length_overrides,
        supplements=payload.supplements,
    )
    return {"content": complete_text(system, user, payload.model)}


@router.post("/jd/match")
def jd_match(payload: MatchReq, _token: str = Depends(require_app_token)) -> dict[str, str]:
    if not payload.jd.strip():
        raise HTTPException(status_code=400, detail="JD 不可空白。")
    if _background_is_empty(payload.background):
        raise HTTPException(status_code=400, detail="請先建立結構化背景。")
    system, user = build_match_prompt(
        structured_background=payload.background,
        target_role=payload.target_role,
        company=payload.company,
        jd=payload.jd,
    )
    return {"content": complete_text(system, user, payload.model, temperature=0.2, json_mode=True)}


@router.post("/resume/onepage")
def resume_onepage(payload: OnePageReq, _token: str = Depends(require_app_token)) -> dict[str, str]:
    system, user = build_one_page_prompt(
        background=payload.background,
        target_role=payload.target_role,
        company=payload.company,
        jd=payload.jd,
        supplements=payload.supplements,
    )
    return {"content": complete_text(system, user, payload.model)}


@router.post("/resume/star")
def resume_star(payload: StarReq, _token: str = Depends(require_app_token)) -> dict[str, str]:
    system, user = build_star_prompt(background=payload.background, target_role=payload.target_role, jd=payload.jd)
    return {"content": complete_text(system, user, payload.model)}


@router.post("/convert")
def resume_convert(payload: ConvertReq, _token: str = Depends(require_app_token)) -> dict[str, str]:
    if payload.mode == "translate":
        system, user = build_convert_translate_prompt(
            original_resume=payload.original_resume,
            from_domain=payload.from_domain,
            to_domain=payload.to_domain,
            target_jd=payload.target_jd,
            background=payload.background,
        )
    elif payload.mode == "rewrite":
        if _background_is_empty(payload.background):
            raise HTTPException(status_code=400, detail="重寫模式需要先建立結構化背景。")
        system, user = build_convert_rewrite_prompt(
            background=payload.background,
            original_resume=payload.original_resume,
            from_domain=payload.from_domain,
            to_domain=payload.to_domain,
            target_jd=payload.target_jd,
        )
    else:
        raise HTTPException(status_code=400, detail="mode 必須是 translate 或 rewrite。")
    return {"content": complete_text(system, user, payload.model)}
