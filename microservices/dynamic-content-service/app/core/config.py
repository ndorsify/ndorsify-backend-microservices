"""Application configuration for dynamic-content-service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "dynamic-content-service"
    # Comma-separated origins allowed to call this service from a browser (CORS).
    cors_origins: str = "http://localhost:3000"
    port: int = 5000
    database_url: str = (
        "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/dynamiccontentdb"
    )
    # Drop connection pooling (serverless instances don't reuse one).
    db_null_pool: bool = False

    # --- Auth (P0) ---
    # Must match users-service so this service can verify access tokens it issues.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"

    # --- Media storage (E7 §1) ---
    # Where uploaded bytes land when BLOB_READ_WRITE_TOKEN is unset: the local
    # filesystem, which keeps dev and tests free of any cloud account.
    media_root: str = "media-store"
    # Set in production (Vercel injects it): uploads go to Vercel Blob instead
    # of the local filesystem, which a serverless instance does not keep.
    blob_read_write_token: str = ""
    media_max_bytes: int = 25 * 1024 * 1024
    # Signed upload/download URLs are short-lived.
    media_url_ttl_seconds: int = 900


settings = Settings()
