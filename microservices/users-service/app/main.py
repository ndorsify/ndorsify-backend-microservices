"""users-service — FastAPI application entrypoint (port 1000)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .db.session import init_db
from .routers import auth, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev/local convenience: ensure tables exist before serving traffic.
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        # Preserve the Java Swagger UI path (springdoc served /api-docs.html).
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
    app.include_router(auth.router)
    app.include_router(users.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "UP", "service": settings.app_name}

    return app


app = create_app()
