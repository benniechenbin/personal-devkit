from __future__ import annotations

from collections.abc import Sequence

import pytest
from retrieval_engine import DocumentChunk
from retrieval_engine.indexing import VectorIndexer


class BadEmbeddingProvider:
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        del texts
        return [[1.0, 2.0, 3.0]]

    def embed_query(self, text: str) -> list[float]:
        del text
        return [1.0, 2.0, 3.0]


class DummyVectorStorage:
    def add_vectors(self, records) -> None:
        del records

    def replace_vectors(self, records) -> None:
        del records

    def query(self, vector, top_k: int = 5):
        del vector, top_k
        return []

    def clear(self) -> None:
        pass


def test_vector_indexer_raises_when_embedding_count_mismatches_documents() -> None:
    documents = [
        DocumentChunk(page_content="first", metadata={"source": "a.md"}),
        DocumentChunk(page_content="second", metadata={"source": "b.md"}),
    ]

    indexer = VectorIndexer(
        storage=DummyVectorStorage(),
        embedding_provider=BadEmbeddingProvider(),
    )

    with pytest.raises(ValueError, match="different vector count"):
        indexer.replace_documents(documents)
