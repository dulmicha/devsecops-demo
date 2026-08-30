import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application configuration settings."""

    app_name: str = Field(default="devsecops-demo", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    app_env: str = Field(
        default_factory=lambda: os.getenv("APP_ENV", "development"),
        description="Runtime environment (development, staging, production)",
    )
    app_port: int = Field(
        default_factory=lambda: int(os.getenv("APP_PORT", "8000")),
        description="Application listening port",
    )
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
        description="Logging level",
    )
    seed_record_count: int = Field(
        default_factory=lambda: int(os.getenv("SEED_RECORD_COUNT", "2500")),
        description="Number of records preloaded on startup",
    )
    default_page_limit: int = 20
    max_page_limit: int = 100


settings = Settings()
