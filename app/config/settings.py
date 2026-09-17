from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database Config ---
    DATABASE_URL: str
    
    # --- App identity ---
    APP_NAME: str = "LeadHawk Account API"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    # --- Password hashing ---
    PASSWORD_HASH_SCHEME: Literal["pbkdf2_sha256"] = "pbkdf2_sha256"
    PASSWORD_HASH_ALGORITHM: Literal["sha256"] = "sha256"
    PASSWORD_HASH_ITERATIONS: int = 600_000

    # --- Authentication ---
    JWT_SECRET_KEY: str = "change-this-development-secret-before-production"
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # --- SMTP ---
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_TIMEOUT_SECONDS: float = 10.0

    # --- Lead discovery (Agent 1) ---
    GOOGLE_PLACES_API_KEY: str = ""
    # A listing is kept as a lead if it falls short on rating, review count,
    # or has no/a broken website (any one of these is enough).
    LEAD_MIN_RATING: float = 3.5
    LEAD_MIN_REVIEWS: int = 10

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENVIRONMENT == "production" and self.JWT_SECRET_KEY == "change-this-development-secret-before-production":
            raise ValueError("JWT_SECRET_KEY must be changed in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so the .env file is parsed once per process, and so every part of
    the app (routes, services, tools) shares the same configuration object
    instead of each re-reading the environment.
    """
    return Settings()
