from collections.abc import Sequence

from retrieval_sdk import DocumentChunk, ScoredDocument, VectorRecord
from retrieval_sdk.indexing import VectorIndexer, build_vector_records
from retrieval_sdk.retrieval import BM25Retriever, HybridRetriever, VectorRetriever


class ToyEmbeddingProvider:
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        tokens = text.lower().split()
        return [
            float(len(tokens)),
            float(tokens.count("risk")),
            float(tokens.count("graph")),
        ]


class MemoryVectorStorage:
    def __init__(self) -> None:
        self.records: list[VectorRecord] = []

    def add_vectors(self, records: Sequence[VectorRecord]) -> None:
        self.records.extend(records)

    def replace_vectors(self, records: Sequence[VectorRecord]) -> None:
        self.records = list(records)

    def query(self, vector: Sequence[float], top_k: int = 5) -> list[ScoredDocument]:
        scored = [
            ScoredDocument(
                document=record.document,
                score=sum(
                    left * right
                    for left, right in zip(vector, record.vector, strict=False)
                ),
                source="memory-vector",
            )
            for record in self.records
        ]
        return sorted(scored, key=lambda item: item.score or 0.0, reverse=True)[:top_k]

    def clear(self) -> None:
        self.records = []


class ToyReranker:
    def score(self, query: str, documents: Sequence[DocumentChunk]) -> list[float]:
        return [
            2.0 if "graph" in document.page_content.lower() else 1.0
            for document in documents
        ]


def test_build_vector_records_uses_external_embedding_provider() -> None:
    documents = [
        DocumentChunk("risk graph", {"source": "a.md"}),
        DocumentChunk("plain note", {"source": "b.md"}),
    ]

    records = build_vector_records(
        documents,
        ToyEmbeddingProvider(),
        batch_size=1,
        id_factory=iter(["a", "b"]).__next__,
    )

    assert [record.id for record in records] == ["a", "b"]
    assert records[0].vector == [2.0, 1.0, 1.0]


def test_vector_indexer_and_retriever_round_trip() -> None:
    storage = MemoryVectorStorage()
    documents = [
        DocumentChunk("risk graph", {"source": "a.md"}),
        DocumentChunk("plain note", {"source": "b.md"}),
    ]

    VectorIndexer(
        storage=storage,
        embedding_provider=ToyEmbeddingProvider(),
        id_factory=iter(["a", "b"]).__next__,
    ).replace_documents(documents)

    results = VectorRetriever(
        storage=storage,
        embedding_provider=ToyEmbeddingProvider(),
    ).search("risk", top_k=1)

    assert results[0].document.metadata["source"] == "a.md"


def test_hybrid_retriever_merges_reranks_and_deduplicates() -> None:
    documents = [
        DocumentChunk("risk graph evidence", {"source": "graph.md"}),
        DocumentChunk("risk checklist", {"source": "risk.md"}),
    ]
    storage = MemoryVectorStorage()
    VectorIndexer(
        storage=storage,
        embedding_provider=ToyEmbeddingProvider(),
    ).replace_documents(documents)

    hybrid = HybridRetriever(
        retrievers=[
            VectorRetriever(storage=storage, embedding_provider=ToyEmbeddingProvider()),
            BM25Retriever(
                documents,
                tokenizer=lambda text: text.lower().split(),
            ),
        ],
        reranker=ToyReranker(),
    )

    results = hybrid.search("risk graph", top_k=2)

    assert [document.metadata["source"] for document in results] == [
        "graph.md",
        "risk.md",
    ]
    assert results[0].metadata["rerank_score"] == 2.0
