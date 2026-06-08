from __future__ import annotations

from collections.abc import Callable, Sequence

from retrieval_engine.domain import GraphContext, GraphRelationshipHit
from retrieval_engine.providers import EmbeddingProvider
from retrieval_engine.storage import GraphVectorStorage

SemanticRelationshipFormatter = Callable[[Sequence[GraphRelationshipHit]], str]


class SemanticGraphRetriever:
    """通过实体向量搜索召回图谱上下文。"""

    def __init__(
        self,
        storage: GraphVectorStorage,
        embedding_provider: EmbeddingProvider,
        *,
        formatter: SemanticRelationshipFormatter | None = None,
        entity_limit: int = 5,
    ) -> None:
        self.storage = storage
        self.embedding_provider = embedding_provider
        self.formatter = formatter or format_semantic_relationship_hits
        self.entity_limit = entity_limit

    def search(self, query: str, limit: int = 20) -> GraphContext:
        if not query.strip():
            return GraphContext()
        vector = self.embedding_provider.embed_query(query)
        hits = self.storage.search_relationships_by_vector(
            vector,
            entity_limit=self.entity_limit,
            relationship_limit=limit,
        )
        return GraphContext(relationships=self.formatter(hits))


def format_semantic_relationship_hits(hits: Sequence[GraphRelationshipHit]) -> str:
    if not hits:
        return ""

    lines = ["【语义图谱线索】"]
    for hit in hits:
        source_summary = f"({hit.source_summary})" if hit.source_summary else ""
        target_summary = f"({hit.target_summary})" if hit.target_summary else ""
        score = f" [score={hit.score:.3f}]" if hit.score is not None else ""
        lines.append(
            f"[{hit.source}] {source_summary} --({hit.relation})--> "
            f"[{hit.target}] {target_summary}{score}"
        )
    return "\n".join(lines)
