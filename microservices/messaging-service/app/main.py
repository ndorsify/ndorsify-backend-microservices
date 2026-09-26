"""messaging-service — FastAPI application entrypoint (port 3000).

1:1 direct messaging (P0). See
docs/plans/technical-specifications/p0-foundation.md §3.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
        root_path=settings.root_path,
        docs_url="/api-docs.html",
        openapi_url="/api-docs.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(messaging.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "UP", "service": settings.app_name}

    return app


app = create_app()
