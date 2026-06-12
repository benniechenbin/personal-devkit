from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from provider_engine.schema import ChatMessage

MessageLike = ChatMessage | dict[str, Any]


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for chat completion providers."""

    def complete(self, messages: Sequence[MessageLike], **kwargs: Any) -> str: ...


@runtime_checkable
class AsyncLLMProvider(Protocol):
    """Async protocol for chat completion providers."""

    async def acomplete(self, messages: Sequence[MessageLike], **kwargs: Any) -> str: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for text embedding providers."""

    def embed_documents(self, texts: Sequence[str], **kwargs: Any) -> list[list[float]]: ...
    def embed_query(self, text: str, **kwargs: Any) -> list[float]: ...


@runtime_checkable
class AsyncEmbeddingProvider(Protocol):
    """Async protocol for text embedding providers."""

    async def aembed_documents(self, texts: Sequence[str], **kwargs: Any) -> list[list[float]]: ...
    async def aembed_query(self, text: str, **kwargs: Any) -> list[float]: ...


@runtime_checkable
class RerankerProvider(Protocol):
    """Protocol for reranking providers."""

    def score(self, query: str, documents: Sequence[Any], **kwargs: Any) -> list[float]: ...
