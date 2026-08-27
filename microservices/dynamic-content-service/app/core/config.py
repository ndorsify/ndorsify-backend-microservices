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


settings = Settings()
