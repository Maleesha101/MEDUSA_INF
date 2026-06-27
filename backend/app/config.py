import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
      # Core
      PROJECT_NAME: str = "MEDUSA CTF Platform"
      API_V1_STR: str = "/api/v1"
      DEBUG: bool = False

      # Database
      POSTGRES_DSN: str = os.getenv(
          "POSTGRES_DSN",
          "postgresql+asyncpg://medusa:medusa@postgres:5432/medusa"
      )
      # Redis (for rate‑limit, token blacklist, WS Pub/Sub)
      REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

      # JWT
      JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change‑me‑in‑prod")
      JWT_ALGORITHM: str = "RS256"
      ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
      REFRESH_TOKEN_EXPIRE_DAYS: int = 7

      # Challenge container defaults
      CHALLENGE_IMAGE_PREFIX: str = "medusa/challenge-"
      CONTAINER_CPU_LIMIT: str = "1.0"
      CONTAINER_MEM_LIMIT: str = "512m"

      # Misc
      LOG_LEVEL: str = "info"

      model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

