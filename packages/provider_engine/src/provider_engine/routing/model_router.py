from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from provider_engine.errors import ProviderRouteError
from provider_engine.protocols import EmbeddingProvider, LLMProvider, MessageLike

ProviderT = TypeVar("ProviderT")


@dataclass(slots=True)
class ModelRoute(Generic[ProviderT]):
    provider: ProviderT
    model: str | None = None
    options: dict[str, Any] = field(default_factory=dict)

    def merged_options(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        merged = dict(self.options)
        if self.model is not None:
            merged["model"] = self.model
        merged.update(kwargs)
        return merged


class ModelRouter:
    """Small named router for app and agent model policies."""

    def __init__(self) -> None:
        self._llms: dict[str, ModelRoute[LLMProvider]] = {}
        self._embeddings: dict[str, ModelRoute[EmbeddingProvider]] = {}

    def register_llm(
        self,
        name: str,
        provider: LLMProvider,
        *,
        model: str | None = None,
        **options: Any,
    ) -> None:
        self._llms[name] = ModelRoute(provider=provider, model=model, options=options)

    def register_embedding(
        self,
        name: str,
        provider: EmbeddingProvider,
        *,
        model: str | None = None,
        **options: Any,
    ) -> None:
        self._embeddings[name] = ModelRoute(provider=provider, model=model, options=options)

    def llm(self, name: str = "default") -> ModelRoute[LLMProvider]:
        try:
            return self._llms[name]
        except KeyError as exc:
            raise ProviderRouteError(f"unknown llm route: {name}") from exc

    def embedding(self, name: str = "default") -> ModelRoute[EmbeddingProvider]:
        try:
            return self._embeddings[name]
        except KeyError as exc:
            raise ProviderRouteError(f"unknown embedding route: {name}") from exc

    def complete(self, name: str, messages: Sequence[MessageLike], **kwargs: Any) -> str:
        route = self.llm(name)
        return route.provider.complete(messages, **route.merged_options(kwargs))

    def embed_query(self, name: str, text: str, **kwargs: Any) -> list[float]:
        route = self.embedding(name)
        return route.provider.embed_query(text, **route.merged_options(kwargs))

    def embed_documents(
        self,
        name: str,
        texts: Sequence[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        route = self.embedding(name)
        return route.provider.embed_documents(texts, **route.merged_options(kwargs))
