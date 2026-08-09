"""
Application configuration loaded from environment variables.

All settings have sensible defaults for local development.
In production, override via environment variables or a .env file.
"""
from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ─────────────────────────────────────────────────────────
    APP_NAME: str = "CloudPilot"
    ENVIRONMENT: str = "development"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://cloudpilot:cloudpilot@localhost:5432/cloudpilot"

    # ── JWT ──────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-insecure-default-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── CORS ─────────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # ── Repository Analyzer (Phase 2) ─────────────────────────────────────────
    MAX_REPO_FILES: int = 10_000          # Maximum files to scan
    MAX_REPO_SIZE_MB: int = 250           # Maximum total repo size in MB
    MAX_FILE_SIZE_KB: int = 2_048         # Maximum individual file size in KB
    GIT_CLONE_TIMEOUT_SECONDS: int = 60   # Seconds before clone is aborted
    ANALYSIS_TIMEOUT_SECONDS: int = 120   # Seconds before analysis is aborted

    # ── AI Architecture Planner (Phase 3) ─────────────────────────────────────
    AI_PROVIDER: str = "mock"              # mock | openai | gemini | openrouter
    AI_MODEL: str = "gpt-4o-mini"
    AI_API_KEY: str = ""
    AI_MAX_RETRIES: int = 2

    # Phase 7 controlled traffic and autoscaling safety limits.
    AUTOSCALING_INTERVAL_SECONDS: int = 10
    AUTOSCALING_MAX_METRIC_AGE_SECONDS: int = 30
    TRAFFIC_MAX_RPS: int = 500
    TRAFFIC_MAX_DURATION_SECONDS: int = 300
    TRAFFIC_MAX_CONCURRENT_RUNS: int = 2

    # Phase 8 is intentionally disabled by default in production.
    FAILURE_INJECTION_ENABLED: bool = True
    FAILURE_MAX_CONCURRENT_INJECTIONS: int = 1
    FAILURE_MAX_DURATION_SECONDS: int = 120
    RECOVERY_MAX_ATTEMPTS: int = 3
    RECOVERY_COOLDOWN_SECONDS: int = 60
    RECOVERY_TIMEOUT_SECONDS: int = 120
    RECOVERY_LOOP_WINDOW_SECONDS: int = 600

    # Phase 9 advisory analysis: bounded, redacted, and never an execution path.
    AI_INCIDENT_TIMEOUT_SECONDS: int = 15
    AI_INCIDENT_MAX_RETRIES: int = 2
    AI_INCIDENT_CONTEXT_LOG_LINES: int = 100
    AI_INCIDENT_CONTEXT_EVENTS: int = 20
    AI_INCIDENT_HISTORY_LIMIT: int = 5

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def allowed_origins(self) -> list[str]:
        return [self.FRONTEND_URL]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
