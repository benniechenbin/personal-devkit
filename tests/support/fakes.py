from __future__ import annotations

from collections.abc import Sequence

from retrieval_engine.domain import (
    CommunityCandidate,
    CommunityDetectionReport,
    CommunitySummary,
    GraphEntity,
    GraphExtraction,
    GraphRelation,
    ScoredDocument,
    VectorRecord,
)


class FakeEmbeddingProvider:
    """稳定、可复现的假 embedding provider。

    用来验证 retrieval_engine 的编排链路，不验证真实 embedding 效果。
    """

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [
            float(len(text)),
            float(text.count("图谱") + text.count("向量") + text.count("GraphRAG")),
            1.0,
        ]


class FakeLLMProvider:
    """稳定、可复现的假 LLM provider。

    根据 prompt 内容返回图谱抽取或社区总结 JSON。
    """

    def complete(self, messages: Sequence[dict[str, str]], **kwargs) -> str:
        del kwargs
        content = "\n".join(message["content"] for message in messages)

        if "知识聚落" in content:
            return """
            {
              "name": "GraphRAG 检索聚落",
              "summary": "围绕向量检索、知识图谱和社区总结的知识聚落。",
              "cluster_type": "技术主题",
              "confidence": 0.9
            }
            """

        return """
        {
          "entities": [
            {
              "id": "GraphRAG",
              "type": "技术",
              "summary": "图谱增强检索方法"
            },
            {
              "id": "Qdrant",
              "type": "向量数据库",
              "summary": "向量存储组件"
            },
            {
              "id": "Neo4j",
              "type": "图数据库",
              "summary": "图谱存储组件"
            }
          ],
          "relationships": [
            {
              "source": "GraphRAG",
              "target": "Qdrant",
              "relation": "使用"
            },
            {
              "source": "GraphRAG",
              "target": "Neo4j",
              "relation": "使用"
            }
          ]
        }
        """


class InMemoryVectorStorage:
    """内存向量存储。

    只用于测试 VectorIndexer / VectorRetriever 能否协作。
    """

    def __init__(self) -> None:
        self.records: list[VectorRecord] = []

    def add_vectors(self, records: Sequence[VectorRecord]) -> None:
        self.records.extend(records)

    def replace_vectors(self, records: Sequence[VectorRecord]) -> None:
        self.records = list(records)

    def query(self, vector: Sequence[float], top_k: int = 5) -> list[ScoredDocument]:
        del vector
        return [
            ScoredDocument(
                document=record.document,
                score=1.0,
                source="in_memory_vector",
            )
            for record in self.records[:top_k]
        ]

    def clear(self) -> None:
        self.records.clear()


class InMemoryGraphWriter:
    """内存图谱写入器。

    注意：GraphIndexer 当前实际会调用 upsert_extraction。
    所以这里必须实现该方法。
    """

    def __init__(self) -> None:
        self.entities: dict[str, GraphEntity] = {}
        self.relations: list[GraphRelation] = []

    def upsert_entity(self, entity: GraphEntity, *, source: str | None = None) -> None:
        del source
        self.entities[entity.id] = entity

    def upsert_relation(
        self,
        relation: GraphRelation,
        *,
        source: str | None = None,
    ) -> None:
        del source
        self.relations.append(relation)

    def upsert_entities(
        self,
        entities: Sequence[GraphEntity],
        *,
        source: str | None = None,
    ) -> None:
        for entity in entities:
            self.upsert_entity(entity, source=source)

    def upsert_relations(
        self,
        relations: Sequence[GraphRelation],
        *,
        source: str | None = None,
    ) -> None:
        for relation in relations:
            self.upsert_relation(relation, source=source)

    def upsert_extraction(
        self,
        extraction: GraphExtraction,
        *,
        source: str | None = None,
    ) -> None:
        self.upsert_entities(extraction.entities, source=source)
        self.upsert_relations(extraction.relationships, source=source)

    def remove_source(self, source: str) -> None:
        del source

    def clear(self) -> None:
        self.entities.clear()
        self.relations.clear()


class InMemoryCommunityStorage:
    """内存社区存储。

    用来测试 CommunityDetector / CommunitySummarizer 编排能否跑通。
    """

    def __init__(self) -> None:
        self.saved_summaries: dict[int | str, CommunitySummary] = {}

    def detect_leiden_communities(
        self,
        *,
        graph_name: str = "knowledge_graph",
        node_label: str = "Entity",
        relationship_type: str = "RELATION",
        write_property: str = "communityId",
        orientation: str = "UNDIRECTED",
        random_seed: int = 42,
        concurrency: int = 1,
        drop_existing_projection: bool = True,
    ) -> CommunityDetectionReport:
        del (
            node_label,
            relationship_type,
            write_property,
            orientation,
            random_seed,
            concurrency,
            drop_existing_projection,
        )
        return CommunityDetectionReport(
            graph_name=graph_name,
            node_count=3,
            relationship_count=2,
            community_count=1,
            node_properties_written=3,
            modularity=0.5,
        )

    def list_unsummarized_communities(
        self,
        *,
        threshold: int = 20,
        top_node_limit: int = 30,
        limit: int | None = None,
    ) -> list[CommunityCandidate]:
        del threshold, top_node_limit, limit
        return [
            CommunityCandidate(
                community_id=1,
                size=3,
                top_nodes=["GraphRAG", "Qdrant", "Neo4j"],
            )
        ]

    def save_community_summary(
        self,
        *,
        community_id: int | str,
        size: int,
        summary: CommunitySummary,
    ) -> None:
        del size
        self.saved_summaries[community_id] = summary
