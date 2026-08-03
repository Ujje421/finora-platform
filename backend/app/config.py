"""
Financial Intelligence Platform — Application Configuration

Uses pydantic-settings for typed, validated environment configuration.
All settings are loaded from environment variables or .env file.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "financial-terminal"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/financial_terminal"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"

    # --- Security ---
    api_key_encryption_key: str = ""
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # --- SEC EDGAR ---
    edgar_user_agent: str = "FinancialTerminal dev@example.com"
    edgar_rate_limit_per_second: int = 10

    # --- Object Storage (R2/S3) ---
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "financial-terminal-raw"
    r2_endpoint_url: str = ""

    # --- AI Providers (internal extraction only) ---
    groq_api_key: str = ""
    gemini_api_key: str = ""

    # --- Embedding Model ---
    embedding_model_name: str = "nomic-ai/nomic-embed-text-v1.5"
    embedding_dimension: int = 768

    # --- Sentry ---
    sentry_dsn: str = ""

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings. Singleton pattern."""
    return Settings()
