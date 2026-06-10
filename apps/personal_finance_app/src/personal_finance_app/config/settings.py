"""App settings and configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


def find_project_root(
    current_path: Path, markers: tuple[str, ...] = ("pyproject.toml", ".git")
) -> Path:
    for parent in current_path.parents:
        if any((parent / marker).exists() for marker in markers):
            return parent
    return current_path.parent


BASE_DIR = find_project_root(Path(__file__).resolve())


class Settings(BaseSettings):
    """
    Settings defined here will be automatically parsed from environment variables
    or from the local .env file. Pydantic handles type coercion and validation.
    """

    app_name: str = "personal-finance-app"
    app_env: Literal["development", "test", "production"] = "development"

    log_dir: Path = Path("logs")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # OpenAI configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_log_dir(self) -> Path:
        if self.log_dir.is_absolute():
            return self.log_dir
        return BASE_DIR / self.log_dir


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
