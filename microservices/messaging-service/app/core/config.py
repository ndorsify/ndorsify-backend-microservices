"""Application configuration for messaging-service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "messaging-service"
    port: int = 3000
    database_url: str = "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/messagingdb"

    # --- Auth ---
    # Must match users-service so this service can verify access tokens.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"


settings = Settings()
