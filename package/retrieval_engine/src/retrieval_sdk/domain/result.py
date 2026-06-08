from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from retrieval_sdk.domain.document import DocumentChunk


@dataclass(slots=True)
class ScoredDocument:
    document: DocumentChunk
    score: float | None = None
    source: str = ""


@dataclass(slots=True)
class SearchResult:
    content: str
    source: str
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BuildReport:
    total_documents: int = 0
    total_chunks: int = 0
    created: int = 0
    updated: int = 0
    deleted: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
