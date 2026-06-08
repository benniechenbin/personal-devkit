from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.enums import AppEnv, ModelProvider


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
        populate_by_name=True,
    )

    app_name: str = Field(
        default="agent-enterprise-boilerplate",
        description="应用名称，用于日志与运行时元数据。",
    )
    app_env: AppEnv = Field(
        default=AppEnv.DEV,
        description="运行环境，可选值：development、testing、production。",
    )

    log_dir: Path = Field(
        default=Path("logs"),
        description="日志目录；相对路径基于当前工作目录解析。",
    )
    log_level: str = Field(
        default="INFO",
        description="日志级别，例如 DEBUG、INFO、WARNING、ERROR 或 CRITICAL。",
    )

    log_format: Literal["auto", "pretty", "json"] = Field(
        default="auto",
        description="日志格式；auto 在开发环境使用易读格式，在生产环境使用 JSON 格式。",
    )

    default_model_provider: ModelProvider = Field(
        default=ModelProvider.OPENAI,
        description="默认模型提供商。",
    )
    model_name: str = Field(
        default="gpt-4o-mini",
        description="默认模型名称。",
    )
    openai_api_key: SecretStr | None = Field(
        default=None,
        description="OpenAI API 密钥。",
    )
    openai_api_base: str | None = Field(
        default=None,
        description="可选的 OpenAI 兼容 API 基础地址。",
    )

    anthropic_api_key: SecretStr | None = Field(
        default=None,
        description="Anthropic API 密钥。",
    )
    google_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        description="Google 或 Gemini API 密钥；优先使用 GOOGLE_API_KEY。",
    )
    deepseek_api_key: SecretStr | None = Field(
        default=None,
        description="DeepSeek API 密钥。",
    )
    tavily_api_key: SecretStr | None = Field(
        default=None,
        description="可选搜索集成使用的 Tavily API 密钥。",
    )

    @property
    def resolved_log_dir(self) -> Path:
        if self.log_dir.is_absolute():
            return self.log_dir
        return BASE_DIR / self.log_dir

    def require_provider_credentials(self, provider: ModelProvider | None = None) -> None:
        selected_provider = provider or self.default_model_provider
        provider_keys: dict[ModelProvider, tuple[SecretStr | None, str]] = {
            ModelProvider.OPENAI: (self.openai_api_key, "OPENAI_API_KEY"),
            ModelProvider.ANTHROPIC: (self.anthropic_api_key, "ANTHROPIC_API_KEY"),
            ModelProvider.GOOGLE: (self.google_api_key, "GOOGLE_API_KEY"),
            ModelProvider.DEEPSEEK: (self.deepseek_api_key, "DEEPSEEK_API_KEY"),
        }
        api_key, env_name = provider_keys[selected_provider]
        if api_key is None or not api_key.get_secret_value():
            raise ValueError(f"{selected_provider.value} provider requires {env_name}.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
