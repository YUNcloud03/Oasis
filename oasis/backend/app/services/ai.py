from fastapi import HTTPException

from app.core.config import get_settings


ALLOWED_MODELS = {"gpt-4o", "gpt-4o-mini", "gpt-4-turbo"}


def complete_text(
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.35,
    json_mode: bool = False,
) -> str:
    settings = get_settings()
    selected_model = model or settings.openai_model
    if selected_model not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail="不支援的 AI model。")
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="後端尚未設定 OPENAI_API_KEY，無法呼叫 AI 生成。")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    kwargs = {
        "model": selected_model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI 呼叫失敗：{exc}") from exc
    content = response.choices[0].message.content
    return content.strip() if content else ""
