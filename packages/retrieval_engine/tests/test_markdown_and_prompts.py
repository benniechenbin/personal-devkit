from retrieval_engine.loaders import MarkdownLoader
from retrieval_engine.parsers import parse_frontmatter
from retrieval_engine.prompts import render_prompt


def test_parse_frontmatter_returns_metadata_and_body() -> None:
    metadata, body = parse_frontmatter(
        "---\ndate: 2026/06/07\ntags: [risk, graph]\n---\n# Note\nProject risk."
    )

    assert metadata["date"] == "2026-06-07"
    assert metadata["tags"] == ["risk", "graph"]
    assert body == "# Note\nProject risk."


def test_markdown_loader_keeps_whole_document(tmp_path) -> None:
    source_dir = tmp_path / "docs"
    source_dir.mkdir()
    (source_dir / "risk.md").write_text(
        "---\ntags: [risk]\n---\n# Risk\n\n## Evidence\n\nLong body.",
        encoding="utf-8",
    )
    ignored_dir = source_dir / ".obsidian"
    ignored_dir.mkdir()
    (ignored_dir / "ignored.md").write_text("ignored", encoding="utf-8")

    documents = MarkdownLoader(source_dir).load()

    assert len(documents) == 1
    assert documents[0].page_content == "# Risk\n\n## Evidence\n\nLong body."
    assert documents[0].metadata["source"] == "risk.md"
    assert documents[0].metadata["relative_path"] == "risk.md"


def test_render_prompt_replaces_simple_variables() -> None:
    assert (
        render_prompt("Extract {{ topic }} from {{ source }}.", topic="risk", source="docs")
        == "Extract risk from docs."
    )
