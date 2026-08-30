"""discovery-service — FastAPI application entrypoint (port 9000).

Creator search + brand shortlists (P0), over a local creator index. See
docs/plans/technical-specifications/p0-foundation.md §4.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .db.seed import seed_creator_index
from .db.session import init_db
from .routers import discovery, internal


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if settings.seed_on_start:
        await seed_creator_index()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
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
    app.include_router(discovery.router)
    app.include_router(internal.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "UP", "service": settings.app_name}

    return app


app = create_app()
