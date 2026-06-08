from __future__ import annotations

from retrieval_sdk.domain import DocumentChunk, ScoredDocument
from retrieval_sdk.retrieval import HybridRetriever, Retriever


class FakeScoredRetriever:
    def search(self, query: str, top_k: int = 5) -> list[ScoredDocument]:
        del query
        return [
            ScoredDocument(
                document=DocumentChunk(
                    page_content="alpha",
                    metadata={"source": "fake"},
                ),
                score=1.0,
                source="fake",
            )
        ][:top_k]


class FakeDocumentRetriever:
    def search(self, query: str, top_k: int = 5) -> list[DocumentChunk]:
        del query
        return [
            DocumentChunk(
                page_content="beta",
                metadata={"source": "doc"},
            )
        ][:top_k]


def test_fake_retriever_matches_protocol() -> None:
    assert isinstance(FakeScoredRetriever(), Retriever)


def test_hybrid_retriever_accepts_retriever_protocol() -> None:
    retriever = HybridRetriever(
        retrievers=[
            FakeScoredRetriever(),
            FakeDocumentRetriever(),
        ],
        reranker=None,
    )

    results = retriever.search("test", top_k=2)

    assert [document.page_content for document in results] == ["alpha", "beta"]