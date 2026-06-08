from __future__ import annotations

from document_engine.assembler import DocumentAssembler
from document_engine.formatters.markdown_formatter import MarkdownFormatter
from retrieval_engine import DocumentChunk
from retrieval_engine.indexing import VectorIndexer
from retrieval_engine.retrieval import VectorRetriever


def test_document_fragments_can_flow_into_retrieval(
    sample_fragments,
    fake_embedding_provider,
    in_memory_vector_storage,
) -> None:
    # 1. document_engine: Fragment -> Markdown
    raw_markdown = DocumentAssembler().assemble(sample_fragments)
    cleaned_markdown = MarkdownFormatter().format_to_markdown(raw_markdown)

    assert "GraphRAG" in cleaned_markdown
    assert "Qdrant" in cleaned_markdown

    # 2. adapter layer: Markdown -> DocumentChunk
    document = DocumentChunk(
        page_content=cleaned_markdown,
        metadata={
            "source": "document_engine_smoke.md",
            "pipeline": "document_to_retrieval",
        },
    )

    # 3. retrieval_engine: DocumentChunk -> Vector Index
    VectorIndexer(
        storage=in_memory_vector_storage,
        embedding_provider=fake_embedding_provider,
    ).replace_documents([document])

    assert len(in_memory_vector_storage.records) == 1

    # 4. retrieval_engine: Vector Search
    retriever = VectorRetriever(
        storage=in_memory_vector_storage,
        embedding_provider=fake_embedding_provider,
    )
    results = retriever.search("GraphRAG 和向量数据库", top_k=1)

    assert len(results) == 1
    assert "GraphRAG" in results[0].document.page_content