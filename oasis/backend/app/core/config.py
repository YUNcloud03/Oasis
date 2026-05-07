from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OASIS Backend"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./oasis.db"
    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    default_locale: str = "zh-TW"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    app_token: str = "dev-oasis-token"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
