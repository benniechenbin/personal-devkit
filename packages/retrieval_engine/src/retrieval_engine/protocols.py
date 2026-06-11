from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from retrieval_engine.domain import (
    CommunityDetectionReport,
    CommunitySummary,
    DocumentChunk,
    GraphCommunityHit,
    GraphExtraction,
    GraphRelationshipHit,
    ScoredDocument,
    VectorRecord,
)


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for text embedding providers."""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM chat completion providers."""

    def complete(self, messages: Sequence[dict[str, str]], **kwargs: Any) -> str: ...


@runtime_checkable
class RerankerProvider(Protocol):
    """Protocol for reranking providers."""

    def score(self, query: str, documents: Sequence[DocumentChunk]) -> list[float]: ...


@runtime_checkable
class VectorStorage(Protocol):
    """Protocol for vector storage backends."""

    def add_vectors(self, records: Sequence[VectorRecord]) -> None: ...
    def replace_vectors(self, records: Sequence[VectorRecord]) -> None: ...
    def query(self, vector: Sequence[float], top_k: int = 5) -> list[ScoredDocument]: ...
    def clear(self) -> None: ...


@runtime_checkable
class GraphWriter(Protocol):
    """Protocol for graph write backends."""

    def upsert_extraction(
        self,
        extraction: GraphExtraction,
        *,
        source: str | None = None,
    ) -> None: ...

    def remove_source(self, source: str) -> None: ...
    def clear(self) -> None: ...


@runtime_checkable
class GraphStorage(Protocol):
    """Protocol for graph read backends."""

    def search_relationships(self, keyword: str, limit: int = 20) -> list[GraphRelationshipHit]: ...
    def search_communities(self, keyword: str, limit: int = 3) -> list[GraphCommunityHit]: ...


@runtime_checkable
class CommunityStorage(Protocol):
    """Protocol for community detection and summary storage backends."""

    def detect_leiden_communities(self, **kwargs: Any) -> CommunityDetectionReport: ...

    def save_community_summary(
        self,
        community_id: int | str,
        size: int,
        summary: CommunitySummary,
    ) -> None: ...
