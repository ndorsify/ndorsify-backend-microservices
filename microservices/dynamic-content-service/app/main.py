"""dynamic-content-service — FastAPI application entrypoint (port 5000)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.config import settings
from .db.session import init_db
from .routers import onboarding


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
    app.include_router(onboarding.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "UP", "service": settings.app_name}

    return app


app = create_app()
