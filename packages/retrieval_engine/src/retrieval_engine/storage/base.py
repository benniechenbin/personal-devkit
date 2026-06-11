from __future__ import annotations

from retrieval_engine.domain import DocumentChunk
from retrieval_engine.protocols import VectorStorage as VectorStorageProtocol

NativeDocument = DocumentChunk
VectorStorage = VectorStorageProtocol


class VectorStore:
    """旧版包装类，建议逐步迁移到直接使用 VectorStorage 和 Indexer/Retriever。"""

    ...
