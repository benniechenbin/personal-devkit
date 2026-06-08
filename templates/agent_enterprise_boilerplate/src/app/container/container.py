from functools import cached_property
from typing import Any

from app.config.enums import ModelProvider
from app.config.settings import Settings, get_settings
from app.tools.registry import ToolRegistry


class Container:
    """显式装配应用资源的容器。"""

    def __init__(
        self,
        app_settings: Settings | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.settings = app_settings or get_settings()
        self.tools = tool_registry or ToolRegistry()

    @classmethod
    def build(
        cls,
        app_settings: Settings | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> "Container":
        return cls(
            app_settings=app_settings or get_settings(),
            tool_registry=tool_registry,
        )

    def validate(self) -> None:
        self.settings.require_provider_credentials()
        if self.settings.default_model_provider != ModelProvider.OPENAI:
            raise ValueError(
                f"Unsupported model provider: {self.settings.default_model_provider.value}"
            )

    @cached_property
    def llm(self) -> Any:
        if self.settings.default_model_provider == ModelProvider.OPENAI:
            try:
                from langchain_openai import ChatOpenAI
            except ImportError as exc:
                message = "Install langchain-openai before using the LLM service."
                raise RuntimeError(message) from exc

            return ChatOpenAI(
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_api_base,
                model=self.settings.model_name,
            )
        raise ValueError(
            f"Unsupported model provider: {self.settings.default_model_provider.value}"
        )
