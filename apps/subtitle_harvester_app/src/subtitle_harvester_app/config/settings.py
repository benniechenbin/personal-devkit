from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_project_root(
    current_path: Path, markers: tuple[str, ...] = ("pyproject.toml", "requirements.txt", ".git")
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
        description="应用名称，用于启动横幅和日志标识。",
    )
    app_env: Literal["development", "test", "production"] = Field(
        default="development",
        description="运行环境，可选值：development、test、production。",
    )

    log_dir: Path = Field(
        default=Path("logs"),
        description="日志目录。相对路径会基于项目根目录解析。",
    )
    output_dir: Path = Field(
        default=Path("output"),
        description="输出文件目录。相对路径会基于项目根目录解析。",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="日志级别，可选值：DEBUG、INFO、WARNING、ERROR、CRITICAL。",
    )
    tmdb_api_key: SecretStr | None = Field(
        default=None,
        description="TMDb API Read Access Token，用于 Authorization Bearer。",
    )
    tmdb_language: str = "zh-CN"
    tmdb_region: str = "CN"
    tmdb_max_pages: int = 3

    @property
    def resolved_log_dir(self) -> Path:
        if self.log_dir.is_absolute():
            return self.log_dir
        return BASE_DIR / self.log_dir

    @property
    def resolved_output_dir(self) -> Path:
        return self.output_dir if self.output_dir.is_absolute() else BASE_DIR / self.output_dir


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
