"""
TOEFL Teacher Bot — application-wide configuration.

All values are loaded from environment variables (or .env file)
via pydantic-settings.  No hardcoded secrets.

DATABASE_URL priority:
  1. DATABASE_URL env var (Scalingo sets this automatically)
  2. Composed from POSTGRES_HOST/PORT/USER/PASSWORD/DB (Docker / local)
"""

from __future__ import annotations

import json
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised, validated application config."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Telegram ────────────────────────────────────────────
    bot_token: str

    # ── Database ────────────────────────────────────────────
    # Option A: single URL (Scalingo, Heroku, Railway, …)
    database_url: Optional[str] = None

    # Option B: individual vars (Docker Compose)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "toefl"
    postgres_password: str = "changeme"
    postgres_db: str = "toefl_teacher"

    # ── Ollama ──────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # ── App ─────────────────────────────────────────────────
    log_level: str = "INFO"
    admin_ids: List[int] = []

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, v: str | list) -> list:
        if isinstance(v, str):
            return json.loads(v) if v.strip() else []
        return v

    # ── Derived URLs ────────────────────────────────────────

    @staticmethod
    def _ensure_asyncpg_scheme(url: str) -> str:
        """Convert postgres:// or postgresql:// to postgresql+asyncpg://."""
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def async_database_url(self) -> str:
        """URL for SQLAlchemy async engine (asyncpg driver)."""
        if self.database_url:
            return self._ensure_asyncpg_scheme(self.database_url)
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        """URL for Alembic (sync driver)."""
        if self.database_url:
            url = self.database_url
            # strip asyncpg driver if present, keep plain postgresql://
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql://", 1)
            if url.startswith("postgresql+asyncpg://"):
                return url.replace("postgresql+asyncpg://", "postgresql://", 1)
            return url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()  # singleton
