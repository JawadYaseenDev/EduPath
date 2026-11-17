from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="UNIRAH_", extra="ignore")

    environment: str = "development"
    # SQLite for local development; PostgreSQL (Supabase) in staging/production.
    database_url: str = "sqlite:///./dev.db"
    # MUST be overridden outside development (UNIRAH_JWT_SECRET).
    jwt_secret: str = "dev-only-secret-change-me-0123456789abcdef"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = ["*"]
    # "extended" or "strict_pdf" — see docs/RECOMMENDATION_ENGINE.md § 0.1
    result_mode: str = "extended"
    load_demo_data: bool = True


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.environment != "development" and s.jwt_secret.startswith("dev-only"):
        raise RuntimeError("Set UNIRAH_JWT_SECRET outside development.")
    return s
