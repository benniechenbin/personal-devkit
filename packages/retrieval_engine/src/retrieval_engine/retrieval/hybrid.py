from __future__ import annotations

import difflib
from collections.abc import Sequence

from retrieval_engine.domain import DocumentChunk, ScoredDocument
from retrieval_engine.providers import RerankerProvider
from retrieval_engine.retrieval.base import Retriever, RetrieverResult


class HybridRetriever:
    """合并向量和词法候选，可选重排并去重。"""

    def __init__(
        self,
        *,
        retrievers: Sequence[Retriever],
        reranker: RerankerProvider | None = None,
        recall_multiplier: int = 4,
        min_rerank_score: float | None = -0.5,
        duplicate_threshold: float = 0.85,
    ) -> None:
        self.retrievers = list(retrievers)
        self.reranker = reranker
        self.recall_multiplier = recall_multiplier
        self.min_rerank_score = min_rerank_score
        self.duplicate_threshold = duplicate_threshold

    def search(self, query: str, top_k: int = 5) -> list[DocumentChunk]:
        if not query.strip():
            return []

        recall_k = max(top_k * self.recall_multiplier, top_k)
        candidates = self._collect_candidates(query, recall_k)
        if not candidates:
            return []

        if self.reranker is not None:
            candidates = self._rerank(query, candidates)
        else:
            candidates = sorted(
                candidates,
                key=lambda item: item.score if item.score is not None else 0.0,
                reverse=True,
            )

        return self._deduplicate(candidates, top_k)

    def _collect_candidates(
        self,
        query: str,
        recall_k: int,
    ) -> list[ScoredDocument]:
        by_content: dict[str, ScoredDocument] = {}
        for retriever in self.retrievers:
            search = retriever.search
            for candidate in search(query, top_k=recall_k):
                scored = self._coerce_candidate(candidate)
                content = scored.document.page_content
                existing = by_content.get(content)
                if existing is None or self._score_value(scored) > self._score_value(existing):
                    by_content[content] = scored
        return list(by_content.values())

    def _rerank(
        self,
        query: str,
        candidates: Sequence[ScoredDocument],
    ) -> list[ScoredDocument]:
        documents = [candidate.document for candidate in candidates]
        scores = self.reranker.score(query, documents) if self.reranker else []
        if len(scores) != len(documents):
            raise ValueError("reranker returned a different score count.")

        reranked: list[ScoredDocument] = []
        for candidate, score in zip(candidates, scores, strict=False):
            if self.min_rerank_score is not None and score < self.min_rerank_score:
                continue
            document = self._copy_document(candidate.document)
            document.metadata["rerank_score"] = float(score)
            document.metadata["retrieval_source"] = candidate.source
            reranked.append(
                ScoredDocument(
                    document=document,
                    score=float(score),
                    source="rerank",
                )
            )
        return sorted(reranked, key=lambda item: item.score or 0.0, reverse=True)

    def _deduplicate(
        self,
        candidates: Sequence[ScoredDocument],
        top_k: int,
    ) -> list[DocumentChunk]:
        unique_documents: list[DocumentChunk] = []
        seen_contents: list[str] = []

        for candidate in candidates:
            document = self._copy_document(candidate.document)
            content = document.page_content.strip()
            if not content:
                continue

            is_duplicate = any(
                difflib.SequenceMatcher(None, content, seen).ratio() > self.duplicate_threshold
                for seen in seen_contents
            )
            if is_duplicate:
                continue

            if "retrieval_score" not in document.metadata and candidate.score is not None:
                document.metadata["retrieval_score"] = float(candidate.score)
            if candidate.source and "retrieval_source" not in document.metadata:
                document.metadata["retrieval_source"] = candidate.source

            unique_documents.append(document)
            seen_contents.append(content)

            if len(unique_documents) >= top_k:
                break

        return unique_documents

    def _coerce_candidate(self, candidate: RetrieverResult) -> ScoredDocument:
        if isinstance(candidate, ScoredDocument):
            return candidate
        if isinstance(candidate, DocumentChunk):
            return ScoredDocument(document=candidate)
        raise TypeError(f"Unsupported retriever candidate: {type(candidate)!r}")

    def _copy_document(self, document: DocumentChunk) -> DocumentChunk:
        return DocumentChunk(
            page_content=document.page_content,
            metadata=dict(document.metadata),
        )

    def _score_value(self, scored: ScoredDocument) -> float:
        return scored.score if scored.score is not None else 0.0
