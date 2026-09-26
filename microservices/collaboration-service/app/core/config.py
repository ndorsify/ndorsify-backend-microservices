"""Application configuration for collaboration-service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "collaboration-service"
    port: int = 4000
    database_url: str = "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/collaborationdb"
    # This service's schema in the shared Postgres (see db/session.py).
    db_schema: str = "collaboration"
    # Drop connection pooling (serverless instances don't reuse one).
    db_null_pool: bool = False
    # Comma-separated origins allowed to call this service from a browser (CORS).
    cors_origins: str = "http://localhost:3000"

    # --- Auth ---
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    # Internal collaboration creation (called by campaign-service on acceptance)
    # is guarded by this shared secret rather than a user JWT.
    service_token: str = "dev-service-token-change-me"


settings = Settings()
