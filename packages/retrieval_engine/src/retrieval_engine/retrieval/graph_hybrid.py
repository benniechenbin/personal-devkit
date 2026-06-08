from __future__ import annotations

from rtrieval_engine.domain import GraphContext
from rtrieval_engine.retrieval.graph_community import CommunityGraphRetriever
from rtrieval_engine.retrieval.graph_local import LocalGraphRetriever
from rtrieval_engine.retrieval.graph_semantic import SemanticGraphRetriever


class HybridGraphRetriever:
    """组合局部图谱、语义图谱和可选聚落上下文。"""

    def __init__(
        self,
        *,
        local_retriever: LocalGraphRetriever,
        semantic_retriever: SemanticGraphRetriever | None = None,
        community_retriever: CommunityGraphRetriever | None = None,
        relationship_limit: int = 20,
        semantic_limit: int = 20,
        community_limit: int = 3,
    ) -> None:
        self.local_retriever = local_retriever
        self.semantic_retriever = semantic_retriever
        self.community_retriever = community_retriever
        self.relationship_limit = relationship_limit
        self.semantic_limit = semantic_limit
        self.community_limit = community_limit

    def search(
        self,
        keyword: str,
        *,
        relationship_limit: int | None = None,
        semantic_limit: int | None = None,
        community_limit: int | None = None,
    ) -> GraphContext:
        local_context = self.local_retriever.search(
            keyword,
            limit=relationship_limit or self.relationship_limit,
        )
        relationship_blocks = []
        if local_context.relationships:
            relationship_blocks.append(local_context.relationships)

        if self.semantic_retriever is not None:
            semantic_context = self.semantic_retriever.search(
                keyword,
                limit=semantic_limit or self.semantic_limit,
            )
            if semantic_context.relationships:
                relationship_blocks.append(semantic_context.relationships)

        if self.community_retriever is None:
            return GraphContext(relationships="\n\n".join(relationship_blocks))

        community_context = self.community_retriever.search(
            keyword,
            limit=community_limit or self.community_limit,
        )
        return GraphContext(
            relationships="\n\n".join(relationship_blocks),
            communities=community_context.communities,
        )

    def search_context(
        self,
        keyword: str,
        *,
        relationship_limit: int | None = None,
        semantic_limit: int | None = None,
        community_limit: int | None = None,
    ) -> tuple[str, str]:
        """兼容旧接口的二元组形态：relationships, communities。"""
        return self.search(
            keyword,
            relationship_limit=relationship_limit,
            semantic_limit=semantic_limit,
            community_limit=community_limit,
        ).as_tuple()
