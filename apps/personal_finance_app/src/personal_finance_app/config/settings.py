"""App settings and configuration."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings defined here will be automatically parsed from environment variables
    or from the local .env file. Pydantic handles type coercion and validation.

    See https://docs.pydantic.dev/latest/concepts/pydantic_settings/
    """

    app_name: str = "personal-finance-app"
    app_env: Literal["development", "test", "production"] = "development"

    log_dir: str = "logs"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # OpenAI configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
