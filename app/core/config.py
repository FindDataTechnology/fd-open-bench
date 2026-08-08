from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # General
    debug: bool = False
    version: str = "0.1.0"
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8999
    frontend_port: int = 3118
    api_url: str = "http://localhost:8999"

    # Database (SQLite by default; Postgres still works via DATABASE_URL)
    database_url: str = "sqlite:///./fd_open_bench.db"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Optional single-token API guard (empty = open, local internal tool)
    fd_bench_api_token: str = ""

    # LLM API Keys (optional)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_base: str | None = None
    azure_openai_api_version: str | None = "2023-05-15"

    # DeepEval
    deepeval_platform_url: str = "https://evals.confident.ai"
    deepeval_project_id: str = ""
    deepeval_test_cases_upload_batch_size: int = 25

    # Optional: External services
    webhook_url: str | None = None
    email_smtp_server: str | None = None
    email_smtp_port: int = 587
    email_smtp_username: str | None = None
    email_smtp_password: str | None = None

    # Cost configuration
    default_business_value_per_task: float = 100.0

    # Data retention (days)
    trace_retention_days: int = 90
    result_retention_days: int = 365
    run_retention_days: int = 730

    # Security
    secure_cookies: bool = True
    cors_origins: list[str] = ["http://localhost:3118", "http://localhost:8999"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
