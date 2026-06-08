from __future__ import annotations

from retrieval_engine.indexing import (
    CommunityDetector,
    CommunitySummarizer,
    GraphExtractor,
    GraphIndexer,
    VectorIndexer,
)
from retrieval_engine.retrieval import BM25Retriever, HybridRetriever, VectorRetriever


def test_retrieval_fullchain_in_memory(
    sample_documents,
    fake_embedding_provider,
    fake_llm_provider,
    in_memory_vector_storage,
    in_memory_graph_writer,
    in_memory_community_storage,
) -> None:
    # 1. 向量入库
    vector_records = VectorIndexer(
        storage=in_memory_vector_storage,
        embedding_provider=fake_embedding_provider,
    ).replace_documents(sample_documents)

    assert len(vector_records) == 2
    assert len(in_memory_vector_storage.records) == 2

    # 2. 向量召回
    vector_retriever = VectorRetriever(
        storage=in_memory_vector_storage,
        embedding_provider=fake_embedding_provider,
    )
    vector_results = vector_retriever.search("GraphRAG 如何结合图谱和向量？", top_k=2)

    assert len(vector_results) == 2
    assert vector_results[0].document.page_content

    # 3. 词法召回 + 混合召回
    lexical_retriever = BM25Retriever(sample_documents)
    hybrid_retriever = HybridRetriever(
        retrievers=[
            vector_retriever,
            lexical_retriever,
        ],
    )

    hybrid_results = hybrid_retriever.search("GraphRAG 图谱 向量", top_k=2)

    assert hybrid_results
    assert any("GraphRAG" in document.page_content for document in hybrid_results)

    # 4. 图谱抽取 + 图谱写入
    graph_indexer = GraphIndexer(
        extractor=GraphExtractor(llm_provider=fake_llm_provider),
        writer=in_memory_graph_writer,
    )
    graph_report = graph_indexer.index_documents(sample_documents)

    assert graph_report.total_documents == 2
    assert "GraphRAG" in in_memory_graph_writer.entities
    assert in_memory_graph_writer.relations

    # 5. 社区检测
    community_report = CommunityDetector(
        storage=in_memory_community_storage,
    ).run()

    assert community_report.community_count == 1

    # 6. 社区总结
    summary_report = CommunitySummarizer(
        storage=in_memory_community_storage,
        llm_provider=fake_llm_provider,
        threshold=1,
    ).summarize_pending()

    assert summary_report.updated == 1
    assert in_memory_community_storage.saved_summaries[1].name == "GraphRAG 检索聚落"