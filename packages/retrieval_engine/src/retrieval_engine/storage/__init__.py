"""向量、图谱、词法和缓存后端的存储适配器。"""

from retrieval_engine.storage.base import NativeDocument, VectorStorage, VectorStore
from retrieval_engine.storage.community import CommunityStorage
from retrieval_engine.storage.graph import GraphStorage, GraphVectorStorage
from retrieval_engine.storage.graph_writer import GraphWriter

__all__ = [
    "CommunityStorage",
    "GraphWriter",
    "GraphStorage",
    "GraphVectorStorage",
    "NativeDocument",
    "Neo4jCommunityStorage",
    "Neo4jGraphStorage",
    "Neo4jGraphWriter",
    "QdrantVectorStorage",
    "VectorStorage",
    "VectorStore",
]


def __getattr__(name: str):
    if name == "QdrantVectorStorage":
        from retrieval_engine.storage.qdrant import QdrantVectorStorage

        return QdrantVectorStorage
    if name == "Neo4jGraphStorage":
        from retrieval_engine.storage.neo4j import Neo4jGraphStorage

        return Neo4jGraphStorage
    if name == "Neo4jGraphWriter":
        from retrieval_engine.storage.neo4j_writer import Neo4jGraphWriter

        return Neo4jGraphWriter
    if name == "Neo4jCommunityStorage":
        from retrieval_engine.storage.neo4j_community import Neo4jCommunityStorage

        return Neo4jCommunityStorage
    raise AttributeError(name)
