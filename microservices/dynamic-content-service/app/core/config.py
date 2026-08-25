"""Application configuration for dynamic-content-service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "dynamic-content-service"
    port: int = 5000
    database_url: str = (
        "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/dynamiccontentdb"
    )


settings = Settings()
