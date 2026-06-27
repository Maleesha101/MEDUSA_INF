from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseSettings, Field, PostgresDsn, RedisDsn, validator


class Settings(BaseSettings):
    """Global configuration loaded from environment variables (or .env)."""

    # ── General ──────────────────────────────────────────────────────
    PROJECT_NAME: str = "MEDUSA CTF Platform"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # ── JWT ────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # ── Database ───────────────────────────────────────────────────
    POSTGRES_DSN: PostgresDsn = Field(..., env="POSTGRES_DSN")
    # Example: postgres://medusa:password@postgres:5432/medusa

    # ── Redis (rate‑limit, pub/sub) ──────────────────────────────────
    REDIS_DSN: RedisDsn = Field(..., env="REDIS_DSN")
    # Example: redis://redis:6379/0

    # ── Docker / Challenge orchestration ─────────────────────────────
    CHALLENGE_NETWORK_PREFIX: str = "medusa_challenges"
    CHALLENGE_CONTAINER_PORT: int = 8080
    CHALLENGE_CPU_LIMIT: str = "0.5"      # 0.5 CPU cores per challenge
    CHALLENGE_MEM_LIMIT: str = "256m"    # 256 MiB per challenge

    # ── Monitoring / Logging ───────────────────────────────────────
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── Misc ───────────────────────────────────────────────────────
    ADMIN_EMAIL: str | None = None

    @validator("POSTGRES_DSN", pre=True)
    def _ensure_db_name(cls, v: str) -> str:
        """Append a default DB name if only host/port are given."""
        if "://" not in v:
            raise ValueError("POSTGRES_DSN must be a full DSN")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"


settings = Settings()
