"""Application configuration for profile-service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "profile-service"
    # Comma-separated origins allowed to call this service from a browser (CORS).
    cors_origins: str = "http://localhost:3000"
    # Public path prefix this service is served under. Deployed, the edge
    # strips /api before the request arrives, so the app never sees it — but
    # any URL it *generates* has to carry it, or the caller gets a 404.
    root_path: str = ""
    port: int = 6060
    database_url: str = "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/profiledb"
    # This service's schema in the shared Postgres (see db/session.py).
    db_schema: str = "profile"
    # Drop connection pooling (serverless instances don't reuse one).
    db_null_pool: bool = False

    # --- Auth (P0) ---
    # Must match users-service so this service can verify access tokens it issues.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"

    # --- Discovery ingest (best-effort) ---
    # When a creator saves their profile we push it to discovery-service's
    # creator index so they become searchable. Unset URL disables the call
    # (tests / isolated runs). Token must match discovery-service's SERVICE_TOKEN.
    discovery_url: str = ""
    service_token: str = "dev-service-token-change-me"


settings = Settings()
