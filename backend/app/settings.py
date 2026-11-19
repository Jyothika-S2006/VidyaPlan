"""Application settings loaded from environment variables."""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env from the repo root (two levels up from this file)
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    """All configuration loaded from .env or environment."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./vidyaplan.db"

    # watsonx.ai
    watsonx_api_key: str = ""
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"
    watsonx_project_id: str = ""
    watsonx_model_id: str = "ibm/granite-13b-instruct-v2"
    llm_timeout_seconds: int = 20
    stress_scenarios: int = 300

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Data
    cohort_size: int = 40
    cohort_seed: int = 42


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
