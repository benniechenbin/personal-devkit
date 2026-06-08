from collections.abc import Sequence

from retrieval_sdk import (
    DocumentChunk,
    GraphEntity,
    GraphExtraction,
    GraphRelation,
)
from retrieval_sdk.indexing import (
    GraphExtractor,
    GraphIndexer,
    SourceCache,
    SourceState,
    hash_text,
)
from retrieval_sdk.parsers import parse_graph_extraction


class FakeLLMProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.messages: list[dict[str, str]] = []

    def complete(self, messages: Sequence[dict[str, str]], **kwargs) -> str:
        self.messages = list(messages)
        return self.response


class FakeGraphWriter:
    def __init__(self) -> None:
        self.extractions: list[tuple[GraphExtraction, str | None]] = []
        self.removed_sources: list[str] = []

    def upsert_extraction(
        self,
        extraction: GraphExtraction,
        *,
        source: str | None = None,
    ) -> None:
        self.extractions.append((extraction, source))

    def remove_source(self, source: str) -> None:
        self.removed_sources.append(source)


def test_parse_graph_extraction_filters_empty_items() -> None:
    extraction = parse_graph_extraction(
        "```json\n"
        "{"
        '"entities": [{"id": "Risk", "type": "Concept"}, {"id": ""}],'
        '"relationships": ['
        '{"source": "Risk", "target": "Project", "relation": "affects"},'
        '{"source": "", "target": "Project", "relation": "mentions"}'
        "]"
        "}"
        "\n```"
    )

    assert extraction.entities == [GraphEntity(id="Risk", type="Concept")]
    assert extraction.relationships == [
        GraphRelation(source="Risk", target="Project", relation="affects")
    ]


def test_graph_extractor_renders_prompt_and_parses_response() -> None:
    llm = FakeLLMProvider('{"entities": [{"id": "Risk", "type": "Concept"}], "relationships": []}')

    extraction = GraphExtractor(
        llm_provider=llm,
        prompt_template="System sees {{ source }}.",
        user_prompt_template="Text: {{ text }}",
    ).extract("risk text", source="risk.md")

    assert extraction.entities[0].id == "Risk"
    assert llm.messages[0]["content"] == "System sees risk.md."
    assert llm.messages[1]["content"] == "Text: risk text"


def test_graph_indexer_writes_extraction_and_reports_counts() -> None:
    llm = FakeLLMProvider(
        '{"entities": [{"id": "Risk", "type": "Concept"}], '
        '"relationships": [{"source": "Risk", "target": "Project", '
        '"relation": "affects"}]}'
    )
    writer = FakeGraphWriter()
    document = DocumentChunk("risk text", {"source": "risk.md"})

    report = GraphIndexer(
        extractor=GraphExtractor(llm_provider=llm),
        writer=writer,
    ).index_documents([document])

    assert report.total_documents == 1
    assert report.created == 1
    assert report.updated == 1
    assert writer.extractions[0][1] == "risk.md"


def test_source_cache_diff_tracks_added_changed_deleted() -> None:
    cache = SourceCache(
        {
            "old.md": SourceState("old.md", "old"),
            "changed.md": SourceState("changed.md", "before"),
            "same.md": SourceState("same.md", "same"),
        }
    )

    diff = cache.diff(
        {
            "new.md": SourceState("new.md", hash_text("new")),
            "changed.md": SourceState("changed.md", "after"),
            "same.md": SourceState("same.md", "same"),
        }
    )

    assert diff.added == ["new.md"]
    assert diff.changed == ["changed.md"]
    assert diff.deleted == ["old.md"]
    assert diff.unchanged == ["same.md"]
    assert diff.to_process == ["new.md", "changed.md"]
    assert diff.to_remove == ["old.md", "changed.md"]
