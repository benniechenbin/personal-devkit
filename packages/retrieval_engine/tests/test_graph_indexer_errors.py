from __future__ import annotations

import pytest
from retrieval_engine import DocumentChunk
from retrieval_engine.domain import GraphEntity, GraphExtraction
from retrieval_engine.indexing import GraphIndexer


class SometimesFailingExtractor:
    def extract(self, text: str, **variables) -> GraphExtraction:
        del variables
        if "bad" in text:
            raise RuntimeError("extract failed")
        return GraphExtraction(
            entities=[
                GraphEntity(
                    id="GraphRAG",
                    type="技术",
                    summary="图谱增强检索方法",
                )
            ],
            relationships=[],
        )


class RecordingGraphWriter:
    def __init__(self) -> None:
        self.extractions: list[GraphExtraction] = []

    def upsert_entity(self, entity, *, source: str | None = None) -> None:
        del entity, source

    def upsert_relation(self, relation, *, source: str | None = None) -> None:
        del relation, source

    def upsert_entities(self, entities, *, source: str | None = None) -> None:
        del entities, source

    def upsert_relations(self, relations, *, source: str | None = None) -> None:
        del relations, source

    def upsert_extraction(
        self,
        extraction: GraphExtraction,
        *,
        source: str | None = None,
    ) -> None:
        del source
        self.extractions.append(extraction)

    def remove_source(self, source: str) -> None:
        del source

    def clear(self) -> None:
        self.extractions.clear()


def test_graph_indexer_collects_errors_when_not_strict() -> None:
    writer = RecordingGraphWriter()
    indexer = GraphIndexer(
        extractor=SometimesFailingExtractor(),
        writer=writer,
        strict=False,
    )

    documents = [
        DocumentChunk(page_content="good document", metadata={"source": "good.md"}),
        DocumentChunk(page_content="bad document", metadata={"source": "bad.md"}),
    ]

    report = indexer.index_documents(documents)

    assert report.total_documents == 2
    assert report.created == 1
    assert report.updated == 0
    assert len(report.errors) == 1
    assert "bad.md" in report.errors[0]
    assert "extract failed" in report.errors[0]
    assert len(writer.extractions) == 1


def test_graph_indexer_raises_when_strict() -> None:
    writer = RecordingGraphWriter()
    indexer = GraphIndexer(
        extractor=SometimesFailingExtractor(),
        writer=writer,
        strict=True,
    )

    documents = [
        DocumentChunk(page_content="bad document", metadata={"source": "bad.md"}),
    ]

    with pytest.raises(RuntimeError, match="extract failed"):
        indexer.index_documents(documents)
