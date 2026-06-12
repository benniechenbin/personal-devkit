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
        description="应用名称，用于日志和运行时元数据。",
    )
    app_env: Literal["development", "test", "production"] = Field(
        default="development",
        description="运行环境：development、test 或 production。",
    )
    log_dir: Path = Field(
        default=Path("logs"),
        description="应用日志目录。相对路径会基于应用根目录解析。",
    )
    output_dir: Path = Field(
        default=Path("output"),
        description=("生成候选 JSON 文件的目录。相对路径会基于应用根目录解析。"),
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="应用日志级别。",
    )
    tmdb_api_key: SecretStr | None = Field(
        default=None,
        description=("TMDb API Key 或 Read Access Token。密钥值不会写入 .env.example。"),
    )
    tmdb_language: str = Field(
        default="zh-CN",
        description="TMDb 响应语言。",
    )
    tmdb_region: str = Field(
        default="CN",
        description="电影发现接口使用的 TMDb 地区。",
    )
    tmdb_max_pages: int = Field(
        default=3,
        ge=1,
        description="每种媒体类型默认抓取的 TMDb 结果页上限。",
    )
    subdl_api_key: SecretStr | None = Field(
        default=None,
        description="SubDL API Key，用于字幕搜索。",
    )
    subdl_languages: str = Field(
        default="ZH,ZH-CN,EN",
        description="SubDL 字幕语言筛选，多个语言用逗号分隔。",
    )
    assrt_token: SecretStr | None = Field(
        default=None,
        description="Assrt / 射手网 API Token，用于字幕搜索。",
    )
    assrt_max_detail_results: int = Field(
        default=5,
        ge=1,
        le=15,
        description="每个候选从 Assrt 搜索结果中最多展开详情的数量。",
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
