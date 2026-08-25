"""Application configuration for profile-service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "profile-service"
    port: int = 6000
    database_url: str = "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/profiledb"


settings = Settings()
