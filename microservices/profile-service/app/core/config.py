"""Application configuration for profile-service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "profile-service"
    # Comma-separated origins allowed to call this service from a browser (CORS).
    cors_origins: str = "http://localhost:3000"
    port: int = 6000
    database_url: str = "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/profiledb"

    # --- Auth (P0) ---
    # Must match users-service so this service can verify access tokens it issues.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"


settings = Settings()
