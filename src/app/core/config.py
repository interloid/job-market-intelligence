from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: SecretStr

    APP_ENV: Literal["development", "test", "production"] = "development"
    DB_ECHO: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    PROJECT_NAME: str = "job-market-intelligence-api"
    PROJECT_DESCRIPTION: str
    VERSION: str = "1.0.0"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    DEBUG: bool = True

    API_PREFIX: str = "/api"
    API_VERSION: str = "v1"
    API_V1_PREFIX: str = f"{API_PREFIX}/{API_VERSION}"

    DB_POOL_SIZE: int = Field(default=5, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=0)
    DB_POOL_RECYCLE: int = Field(default=1800, ge=-1)

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
