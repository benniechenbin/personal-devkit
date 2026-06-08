from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence

from retrieval_engine.domain import DocumentChunk, VectorRecord
from retrieval_engine.providers import EmbeddingProvider
from retrieval_engine.storage import VectorStorage

ProgressCallback = Callable[[int, str], None]
IdFactory = Callable[[], str]


def build_vector_records(
    documents: Sequence[DocumentChunk],
    embedding_provider: EmbeddingProvider,
    *,
    batch_size: int = 64,
    id_factory: IdFactory | None = None,
    progress: ProgressCallback | None = None,
) -> list[VectorRecord]:
    """把文档向量化为可直接入库存储的向量记录。"""
    make_id = id_factory or (lambda: uuid.uuid4().hex)
    records: list[VectorRecord] = []
    total = len(documents)

    if total == 0:
        return records

    for start in range(0, total, batch_size):
        batch = list(documents[start : start + batch_size])
        vectors = embedding_provider.embed_documents([document.page_content for document in batch])
        if len(vectors) != len(batch):
            raise ValueError("embedding_provider returned a different vector count.")

        for document, vector in zip(batch, vectors, strict=False):
            records.append(
                VectorRecord(
                    id=make_id(),
                    vector=[float(value) for value in vector],
                    document=document,
                )
            )

        if progress is not None:
            complete = min(start + len(batch), total)
            progress(complete, f"Embedded {complete}/{total} documents")

    return records


class VectorIndexer:
    """使用 embedding provider 构建向量记录并写入存储。"""

    def __init__(
        self,
        *,
        storage: VectorStorage,
        embedding_provider: EmbeddingProvider,
        batch_size: int = 64,
        id_factory: IdFactory | None = None,
    ) -> None:
        self.storage = storage
        self.embedding_provider = embedding_provider
        self.batch_size = batch_size
        self.id_factory = id_factory

    def add_documents(
        self,
        documents: Sequence[DocumentChunk],
        progress: ProgressCallback | None = None,
    ) -> list[VectorRecord]:
        records = build_vector_records(
            documents,
            self.embedding_provider,
            batch_size=self.batch_size,
            id_factory=self.id_factory,
            progress=progress,
        )
        self.storage.add_vectors(records)
        return records

    def replace_documents(
        self,
        documents: Sequence[DocumentChunk],
        progress: ProgressCallback | None = None,
    ) -> list[VectorRecord]:
        records = build_vector_records(
            documents,
            self.embedding_provider,
            batch_size=self.batch_size,
            id_factory=self.id_factory,
            progress=progress,
        )
        self.storage.replace_vectors(records)
        return records

    def clear(self) -> None:
        self.storage.clear()
