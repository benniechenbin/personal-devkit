from pathlib import Path

from document_engine.readers.docx_reader import DocxReader


def test_docx_reader():
    """测试 DocxReader 功能"""
    reader = DocxReader()
    docx_path = Path(__file__).parent / "data" / "test.docx"
    assert docx_path.exists(), f"测试文件不存在: {docx_path}"
    fragments = reader.parse(docx_path)
    assert len(fragments) >= 1
