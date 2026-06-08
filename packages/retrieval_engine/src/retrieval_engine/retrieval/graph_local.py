from __future__ import annotations

from collections.abc import Callable, Sequence

from rtrieval_engine.domain import GraphContext, GraphRelationshipHit
from rtrieval_engine.storage import GraphStorage

RelationshipFormatter = Callable[[Sequence[GraphRelationshipHit]], str]


class LocalGraphRetriever:
    """召回实体邻域的局部关系上下文。"""

    def __init__(
        self,
        storage: GraphStorage,
        *,
        formatter: RelationshipFormatter | None = None,
    ) -> None:
        self.storage = storage
        self.formatter = formatter or format_relationship_hits

    def search(self, keyword: str, limit: int = 20) -> GraphContext:
        if not keyword.strip():
            return GraphContext()
        hits = self.storage.search_relationships(keyword, limit=limit)
        return GraphContext(relationships=self.formatter(hits))


def format_relationship_hits(hits: Sequence[GraphRelationshipHit]) -> str:
    if not hits:
        return ""

    lines = ["【微观逻辑线索】"]
    for hit in hits:
        source_summary = f"({hit.source_summary})" if hit.source_summary else ""
        target_summary = f"({hit.target_summary})" if hit.target_summary else ""
        lines.append(
            f"[{hit.source}] {source_summary} --({hit.relation})--> [{hit.target}] {target_summary}"
        )
    return "\n".join(lines)
