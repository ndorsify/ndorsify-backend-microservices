"""Application configuration for campaign-service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "campaign-service"
    port: int = 2000
    database_url: str = "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/campaigndb"
    # Comma-separated origins allowed to call this service from a browser (CORS).
    cors_origins: str = "http://localhost:3000"

    # --- Auth ---
    # Must match users-service so this service can verify access tokens.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    # For internal calls this service makes (e.g. creating a collaboration on
    # acceptance).
    service_token: str = "dev-service-token-change-me"
    # collaboration-service base URL; when set, an accepted invitation/application
    # creates a Collaboration there. Empty (default/tests) disables the call.
    collaboration_url: str = ""


settings = Settings()
