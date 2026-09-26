"""Application configuration.

Values come from environment variables (optionally a local ``.env`` file).
The Postgres URL is the production default; tests override ``DATABASE_URL``
to point at a throwaway SQLite database.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "users-service"
    # Comma-separated origins allowed to call this service from a browser (CORS).
    cors_origins: str = "http://localhost:3000"
    port: int = 1000
    # SQLAlchemy async URL. Postgres in prod; SQLite (aiosqlite) in tests.
    database_url: str = "postgresql+asyncpg://ndorsify:ndorsify@localhost:5432/usersdb"
    # Drop connection pooling (serverless instances don't reuse one).
    db_null_pool: bool = False

    # --- Auth (P0) -----------------------------------------------------------
    # JWT_SECRET MUST be overridden per environment. RS256 is an option later
    # (lets other services verify with only the public key); HS256 for now.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    verify_token_hours: int = 48
    reset_token_hours: int = 2
    # Shared secret for internal service-to-service calls (X-Service-Token).
    service_token: str = "dev-service-token-change-me"
    # DEV/TEST ONLY: when true, verify/reset endpoints return the raw token in
    # the response (there is no email provider yet — that arrives with E5).
    expose_dev_tokens: bool = False


settings = Settings()
