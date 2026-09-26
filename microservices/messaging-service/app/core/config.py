"""Application configuration for messaging-service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "messaging-service"
    # Comma-separated origins allowed to call this service from a browser (CORS).
    cors_origins: str = "http://localhost:3000"
    # Public path prefix this service is served under. Deployed, the edge
    # strips /api before the request arrives, so the app never sees it — but
    # any URL it *generates* has to carry it, or the caller gets a 404.
    root_path: str = ""
    port: int = 3000
    database_url: str = "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/messagingdb"
    # This service's schema in the shared Postgres (see db/session.py).
    db_schema: str = "messaging"
    # Drop connection pooling (serverless instances don't reuse one).
    db_null_pool: bool = False

    # --- Auth ---
    # Must match users-service so this service can verify access tokens.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"


settings = Settings()
