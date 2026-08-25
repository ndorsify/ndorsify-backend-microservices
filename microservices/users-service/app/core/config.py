"""Application configuration.

Values come from environment variables (optionally a local ``.env`` file).
The Postgres URL is the production default; tests override ``DATABASE_URL``
to point at a throwaway SQLite database.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "users-service"
    port: int = 1000
    # SQLAlchemy async URL. Postgres in prod; SQLite (aiosqlite) in tests.
    database_url: str = "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/usersdb"


settings = Settings()
