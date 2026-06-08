from __future__ import annotations

from retrieval_engine.domain import ScoredDocument
from retrieval_engine.providers import EmbeddingProvider
from retrieval_engine.storage import VectorStorage


class VectorRetriever:
    """使用外部 embedding provider 查询向量存储。"""

    def __init__(
        self,
        *,
        storage: VectorStorage,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.storage = storage
        self.embedding_provider = embedding_provider

    def search(self, query: str, top_k: int = 5) -> list[ScoredDocument]:
        if not query.strip():
            return []
        query_vector = self.embedding_provider.embed_query(query)
        return self.storage.query(query_vector, top_k=top_k)
