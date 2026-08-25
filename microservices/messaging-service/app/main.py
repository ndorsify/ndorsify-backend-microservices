"""messaging-service — FastAPI application entrypoint (port 3000).

1:1 direct messaging (P0). See
docs/plans/technical-specifications/p0-foundation.md §3.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.config import settings
from .db.session import init_db
from .routers import messaging


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
    app.include_router(messaging.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "UP", "service": settings.app_name}

    return app


app = create_app()
