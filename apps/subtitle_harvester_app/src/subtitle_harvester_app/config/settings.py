from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_project_root(
    current_path: Path,
    markers: tuple[str, ...] = ("pyproject.toml", "requirements.txt", ".git"),
) -> Path:
    for parent in current_path.parents:
        if any((parent / marker).exists() for marker in markers):
            return parent
    return current_path.parent


BASE_DIR = find_project_root(Path(__file__).resolve())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(
        default="subtitle-harvester-app",
        description="Application name used in logs and runtime metadata.",
    )
    app_env: Literal["development", "test", "production"] = Field(
        default="development",
        description="Runtime environment: development, test, or production.",
    )
    log_dir: Path = Field(
        default=Path("logs"),
        description="Directory for application logs. Relative paths resolve from the app root.",
    )
    output_dir: Path = Field(
        default=Path("output"),
        description=(
            "Directory for generated candidate JSON files. "
            "Relative paths resolve from the app root."
        ),
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application log level.",
    )
    tmdb_api_key: SecretStr | None = Field(
        default=None,
        description=(
            "TMDb API key or Read Access Token. Secret values are never written to .env.example."
        ),
    )
    tmdb_language: str = Field(
        default="zh-CN",
        description="TMDb response language.",
    )
    tmdb_region: str = Field(
        default="CN",
        description="TMDb region used for movie discovery.",
    )
    tmdb_max_pages: int = Field(
        default=3,
        ge=1,
        description="Default maximum number of TMDb result pages to fetch per media type.",
    )

    @property
    def resolved_log_dir(self) -> Path:
        if self.log_dir.is_absolute():
            return self.log_dir
        return BASE_DIR / self.log_dir

    @property
    def resolved_output_dir(self) -> Path:
        if self.output_dir.is_absolute():
            return self.output_dir
        return BASE_DIR / self.output_dir


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
