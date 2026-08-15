"""
Clinexa — Application Configuration (Pydantic Settings v2)
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/postgres"

    # Groq
    GROQ_API_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Auth
    JWT_SECRET: str = "change-me-in-production"

    # OCR
    OCR_ENGINE: str = "tesseract"

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # App
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    MAX_UPLOAD_MB: int = 15
    RATE_LIMIT_PER_MINUTE: int = 30

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    @property
    def MAX_UPLOAD_BYTES(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
