from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path

from retrieval_engine.domain import DocumentChunk, ScoredDocument

Tokenizer = Callable[[str], list[str]]


def default_tokenize(text: str) -> list[str]:
    try:
        import jieba
    except ModuleNotFoundError:
        return text.split() or [text]
    return jieba.lcut(text)


class BM25Retriever:
    """词法召回器；安装 rank_bm25 后会使用 BM25 加速。"""

    def __init__(
        self,
        documents: Sequence[DocumentChunk] = (),
        *,
        tokenizer: Tokenizer | None = None,
    ) -> None:
        self.tokenizer = tokenizer or default_tokenize
        self.documents: list[DocumentChunk] = []
        self._model = None
        self.set_corpus(documents)

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        tokenizer: Tokenizer | None = None,
    ) -> BM25Retriever:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        documents = [
            DocumentChunk(
                page_content=item["page_content"],
                metadata=item.get("metadata", {}),
            )
            for item in payload
            if isinstance(item, dict) and isinstance(item.get("page_content"), str)
        ]
        return cls(documents, tokenizer=tokenizer)

    def save(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = destination.with_suffix(destination.suffix + ".tmp")
        payload = [
            {"page_content": document.page_content, "metadata": document.metadata}
            for document in self.documents
        ]
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        temporary_path.replace(destination)

    def set_corpus(self, documents: Sequence[DocumentChunk]) -> None:
        self.documents = list(documents)
        self._model = None
        if not self.documents:
            return

        try:
            from rank_bm25 import BM25Okapi
        except ModuleNotFoundError:
            return

        tokenized = [self.tokenizer(document.page_content) for document in self.documents]
        self._model = BM25Okapi(tokenized)

    def add_documents(self, documents: Sequence[DocumentChunk]) -> None:
        self.set_corpus([*self.documents, *documents])

    def search(self, query: str, top_k: int = 5) -> list[ScoredDocument]:
        if not query.strip() or not self.documents:
            return []
        if self._model is not None:
            return self._search_with_bm25(query, top_k)
        return self._search_with_token_overlap(query, top_k)

    def _search_with_bm25(self, query: str, top_k: int) -> list[ScoredDocument]:
        tokens = self.tokenizer(query)
        scores = self._model.get_scores(tokens)
        ranked = sorted(
            zip(self.documents, scores, strict=False),
            key=lambda item: item[1],
            reverse=True,
        )
        return [
            ScoredDocument(document=document, score=float(score), source="lexical")
            for document, score in ranked[:top_k]
            if score > 0
        ]

    def _search_with_token_overlap(
        self,
        query: str,
        top_k: int,
    ) -> list[ScoredDocument]:
        query_tokens = set(self.tokenizer(query))
        scored: list[ScoredDocument] = []
        for document in self.documents:
            document_tokens = set(self.tokenizer(document.page_content))
            score = len(query_tokens.intersection(document_tokens))
            if score > 0:
                scored.append(
                    ScoredDocument(
                        document=document,
                        score=float(score),
                        source="lexical",
                    )
                )
        return sorted(scored, key=lambda item: item.score or 0.0, reverse=True)[:top_k]
