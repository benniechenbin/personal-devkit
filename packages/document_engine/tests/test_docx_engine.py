from pathlib import Path

from document_engine.engines.docx_engine import DocxEngine


def test_parse_docx():
    engine = DocxEngine()
    docx_path = Path(__file__).parent / "data" / "test.docx"
    fragments = engine.parse(docx_path)

    # 期望：1个段落，1个表格
    assert len(fragments) >= 2

    # 第一个应该是 text
    assert fragments[0].type == "text"
    assert "Hello Docx" in fragments[0].content

    # 第二个应该是 table
    assert fragments[1].type == "table"
    assert "Header1" in fragments[1].content
    assert "Val1" in fragments[1].content
