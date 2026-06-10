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

    app_name: str = Field(
        default="personal-finance-app",
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
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="日志级别，可选值：DEBUG、INFO、WARNING、ERROR、CRITICAL。",
    )

    data_dir: Path = Field(
        default=Path("data"),
        description="数据目录。相对路径会基于项目根目录解析。",
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

    @property
    def resolved_data_dir(self) -> Path:
        if self.data_dir.is_absolute():
            return self.data_dir
        return BASE_DIR / self.data_dir

    @property
    def resolved_db_path(self) -> Path:
        return self.resolved_data_dir / "finance.db"

    @property
    def resolved_report_dir(self) -> Path:
        return self.resolved_data_dir / "reports"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
