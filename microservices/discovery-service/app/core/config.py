"""Application configuration for discovery-service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "discovery-service"
    # Comma-separated origins allowed to call this service from a browser (CORS).
    cors_origins: str = "http://localhost:3000"
    port: int = 9000
    database_url: str = "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/discoverydb"

    # --- Auth ---
    # Must match users-service so this service can verify access tokens.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    # Shared secret for internal service-to-service calls (X-Service-Token).
    # Used by the creator-index ingest endpoint (fed by profile updates).
    service_token: str = "dev-service-token-change-me"

    # Seed a starter creator catalog on startup (dev/demo). Off by default so
    # tests start from an empty index; the local stack enables it.
    seed_on_start: bool = False


settings = Settings()
