from document_engine.assembler import DocumentAssembler
from document_engine.formatters.markdown_formatter import MarkdownFormatter
from document_engine.formatters.obsidian_formatter import ObsidianWrapper
from document_engine.schema import Fragment


def test_document_assembler_sorts_fragments_by_page_and_y() -> None:
    fragments = [
        Fragment(type="text", page_num=1, y0=10, content="第二页"),
        Fragment(type="text", page_num=0, y0=20, content="第一段"),
        Fragment(type="text", page_num=0, y0=10, content="标题"),
    ]

    markdown = DocumentAssembler().assemble(fragments)

    assert markdown.index("标题") < markdown.index("第一段") < markdown.index("第二页")


def test_markdown_formatter_and_obsidian_wrapper() -> None:
    cleaned = MarkdownFormatter().format_to_markdown("标题\n\n\n\n正文")
    wrapped = ObsidianWrapper.inject_yaml_frontmatter(cleaned, "demo.pdf")

    assert "\n\n\n" not in cleaned
    assert 'title: "demo"' in wrapped
    assert "status: unreviewed" in wrapped
