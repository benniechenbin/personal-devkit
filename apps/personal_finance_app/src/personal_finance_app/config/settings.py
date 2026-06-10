from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
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
    """
    应用设置和配置。
    """

    app_name: str = "personal-finance-app"
    app_env: Literal["development", "test", "production"] = "development"

    log_dir: Path = Field(
        default=Path("logs"),
        description="日志目录。相对路径会基于项目根目录解析。",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="日志级别，可选值：DEBUG、INFO、WARNING、ERROR、CRITICAL。",
    )

    # OpenAI configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    llm_url: str = Field(
        default="https://api.openai.com/v1",
        description="LLM API 的基础 URL (例如 DeepSeek 的 https://api.deepseek.com/v1)",
    )

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
