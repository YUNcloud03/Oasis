from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import Base, engine
from app.routers import ai_proxy, applications, auth, companions, fertilizer, garden, jobs, match, profile, resumes


settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="OASIS AI Smart Career Assistant & Growth Garden backend.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "locale": settings.default_locale}

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(ai_proxy.router)
    app.include_router(profile.router, prefix=settings.api_prefix)
    app.include_router(jobs.router, prefix=settings.api_prefix)
    app.include_router(applications.router, prefix=settings.api_prefix)
    app.include_router(garden.router, prefix=settings.api_prefix)
    app.include_router(match.router, prefix=settings.api_prefix)
    app.include_router(resumes.router, prefix=settings.api_prefix)
    app.include_router(companions.router, prefix=settings.api_prefix)
    app.include_router(fertilizer.router, prefix=settings.api_prefix)

    return app


app = create_app()
