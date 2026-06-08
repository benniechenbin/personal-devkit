from collections.abc import Sequence

from retrieval_sdk import (
    CommunityCandidate,
    CommunityDetectionReport,
    CommunitySummary,
    GraphCommunityHit,
    GraphRelationshipHit,
)
from retrieval_sdk.indexing import CommunityDetector, CommunitySummarizer
from retrieval_sdk.retrieval import (
    CommunityGraphRetriever,
    HybridGraphRetriever,
    LocalGraphRetriever,
    SemanticGraphRetriever,
)


class ToyEmbeddingProvider:
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))]


class FakeGraphStorage:
    def search_relationships(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[GraphRelationshipHit]:
        return [
            GraphRelationshipHit(
                source="Risk",
                relation="affects",
                target="Project",
                source_summary="risk source",
            )
        ][:limit]

    def search_communities(
        self,
        keyword: str,
        limit: int = 3,
    ) -> list[GraphCommunityHit]:
        return [
            GraphCommunityHit(
                name="Risk Cluster",
                summary="Project risk context",
                cluster_type="risk",
            )
        ][:limit]

    def search_relationships_by_vector(
        self,
        vector: Sequence[float],
        *,
        entity_limit: int = 5,
        relationship_limit: int = 20,
    ) -> list[GraphRelationshipHit]:
        return [
            GraphRelationshipHit(
                source="Evidence",
                relation="supports",
                target="Risk",
                score=0.9,
            )
        ][:relationship_limit]

    def search_communities_by_vector(
        self,
        vector: Sequence[float],
        *,
        entity_limit: int = 5,
        community_limit: int = 3,
    ) -> list[GraphCommunityHit]:
        return []


class FakeCommunityStorage:
    def __init__(self) -> None:
        self.saved: list[tuple[int | str, CommunitySummary]] = []
        self.detect_options = None

    def detect_leiden_communities(self, **kwargs) -> CommunityDetectionReport:
        self.detect_options = kwargs
        return CommunityDetectionReport(
            graph_name=kwargs["graph_name"], community_count=2
        )

    def list_unsummarized_communities(
        self,
        *,
        threshold: int = 20,
        top_node_limit: int = 30,
        limit: int | None = None,
    ) -> list[CommunityCandidate]:
        return [
            CommunityCandidate(
                community_id=1,
                size=threshold,
                top_nodes=["Risk", "Project"],
            )
        ][:limit]

    def save_community_summary(
        self,
        *,
        community_id: int | str,
        size: int,
        summary: CommunitySummary,
    ) -> None:
        self.saved.append((community_id, summary))


class FakeLLMProvider:
    def complete(self, messages: Sequence[dict[str, str]], **kwargs) -> str:
        assert "Risk" in messages[0]["content"]
        return (
            '{"name": "Risk Cluster", "summary": "Risk context", '
            '"cluster_type": "risk", "confidence": 0.8}'
        )


def test_hybrid_graph_retriever_combines_local_semantic_and_community() -> None:
    storage = FakeGraphStorage()
    retriever = HybridGraphRetriever(
        local_retriever=LocalGraphRetriever(storage),
        semantic_retriever=SemanticGraphRetriever(storage, ToyEmbeddingProvider()),
        community_retriever=CommunityGraphRetriever(storage),
    )

    relationships, communities = retriever.search_context("risk")

    assert "【微观逻辑线索】" in relationships
    assert "【语义图谱线索】" in relationships
    assert "Evidence" in relationships
    assert "【宏观聚落背景】" in communities
    assert "Risk Cluster" in communities


def test_community_detector_passes_options_to_storage() -> None:
    storage = FakeCommunityStorage()

    report = CommunityDetector(
        storage=storage,
        graph_name="project_graph",
        random_seed=7,
    ).run()

    assert report.graph_name == "project_graph"
    assert report.community_count == 2
    assert storage.detect_options["random_seed"] == 7


def test_community_summarizer_saves_llm_summary() -> None:
    storage = FakeCommunityStorage()

    report = CommunitySummarizer(
        storage=storage,
        llm_provider=FakeLLMProvider(),
        threshold=1,
    ).summarize_pending()

    assert report.updated == 1
    assert storage.saved[0][0] == 1
    assert storage.saved[0][1].name == "Risk Cluster"
