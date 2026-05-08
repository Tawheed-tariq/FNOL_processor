"""
Central configuration – all values are driven by environment variables with sensible defaults.
Never hard-code secrets or environment-specific values outside this module.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"          # development | staging | production
    LOG_LEVEL: str = "INFO"

    # ── Ollama / LLM ─────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"           # or "mistral", "phi3", etc.
    OLLAMA_TIMEOUT: int = 120              # seconds
    OLLAMA_MAX_RETRIES: int = 2
    OLLAMA_NO_GPU: bool = True
    OLLAMA_NUM_CTX: int = 2048

    # ── Processing limits ─────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 20
    MAX_BATCH_SIZE: int = 10
    PDF_MAX_PAGES: int = 50

    # ── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["*"]

    # ── Routing thresholds ────────────────────────────────────────────────────
    FAST_TRACK_MAX_CLAIM_AMOUNT: float = 5_000.0
    INVESTIGATION_MIN_CLAIM_AMOUNT: float = 50_000.0
    MISSING_FIELDS_MANUAL_THRESHOLD: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()