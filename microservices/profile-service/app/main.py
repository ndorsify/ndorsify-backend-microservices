"""profile-service — FastAPI application entrypoint (port 6000).

Skeleton service: no domain routes yet (mirrors the original Spring skeleton).
Add models under ``app/models/`` and routers under ``app/routers/`` as the
profile feature is designed.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.config import settings
from .db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        docs_url="/api-docs.html",
        openapi_url="/api-docs.json",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "UP", "service": settings.app_name}

    return app


app = create_app()
